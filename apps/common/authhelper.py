import logging

from django.conf import settings
from django.utils import timezone
from urllib import urlencode
import requests
import json
import time
import uuid

from requests.exceptions import HTTPError

OFFICE_CLIENT_ID = settings.OFFICE_CLIENT_ID
OFFICE_CLIENT_SECRET = settings.OFFICE_CLIENT_SECRET

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET


# The OAuth authority
office_authority = 'https://login.microsoftonline.com'
google_authority = 'https://accounts.google.com'

# The authorize URL
office_authorize_url = '{0}{1}'.format(office_authority, '/common/oauth2/v2.0/authorize?{0}')
google_authorize_url = '{0}{1}'.format(google_authority, '/o/oauth2/v2/auth?{0}')

# The token issuing endpoint
office_token_url = '{0}{1}'.format(office_authority, '/common/oauth2/v2.0/token')
google_token_url = 'https://www.googleapis.com/oauth2/v4/token'

# The scopes required by the app
office_scopes = [
    'openid',
    'offline_access',
    'https://outlook.office.com/calendars.read',
    'https://outlook.office.com/calendars.readwrite',
]
google_scopes = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'email',
    'profile'
]

outlook_api_endpoint = 'https://outlook.office.com/api/v2.0{0}'

logger = logging.getLogger(__name__)

"""
Get Sign url
"""


def get_office_signin_url(redirect_uri):
    # Build the query parameters for the signin url
    params = {
        'client_id': OFFICE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(str(i) for i in office_scopes)
    }

    signin_url = office_authorize_url.format(urlencode(params))

    return signin_url


def get_google_signin_url(redirect_uri):
    # Build the query parameters for the signin url
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(str(i) for i in google_scopes),
        'access_type': 'offline',
        'prompt': 'consent'
    }

    signin_url = google_authorize_url.format(urlencode(params))

    return signin_url

"""
Get Token from auth_code
"""


def get_office_token_from_code(auth_code, redirect_uri):
    # Build the post form for the token request
    post_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in office_scopes),
        'client_id': OFFICE_CLIENT_ID,
        'client_secret': OFFICE_CLIENT_SECRET
    }

    r = requests.post(office_token_url, data=post_data)
    r.raise_for_status()

    try:
        return r.json()
    except:
        return {'error': r.text}


def get_google_token_from_code(auth_code, redirect_uri):
    # Build the post form for the token request
    post_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in google_scopes),
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET
    }

    r = requests.post(google_token_url, data=post_data)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}

"""
Get Token from refresh_token
"""


def get_office_token_from_refresh_token(refresh_token, redirect_uri):
    # Build the post form for the token request
    post_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in office_scopes),
        'client_id': OFFICE_CLIENT_ID,
        'client_secret': OFFICE_CLIENT_SECRET
    }

    r = requests.post(office_token_url, data=post_data)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}


def get_google_token_from_refresh_token(refresh_token, redirect_uri):
    # Build the post form for the token request
    post_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in google_scopes),
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET
    }

    r = requests.post(google_token_url, data=post_data)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}

"""
Get Access_token
"""


def get_office_access_token(request, redirect_uri):
    current_token = request.session['office_access_token']
    expiration = request.session['office_token_expires']
    now = int(time.time())
    if current_token and now < expiration:
        # Token still valid
        return current_token
    else:
        # Token expired
        refresh_token = request.session['office_refresh_token']
        new_tokens = get_office_token_from_refresh_token(refresh_token, redirect_uri)

        # Update session
        # expires_in is in seconds
        # Get current timestamp (seconds since Unix Epoch) and
        # add expires_in to get expiration time
        # Subtract 5 minutes to allow for clock differences
        expiration = int(time.time()) + new_tokens['expires_in'] - 300

        # Save the token in the session
        request.session['office_access_token'] = new_tokens['access_token']
        request.session['office_refresh_token'] = new_tokens['refresh_token']
        request.session['office_token_expires'] = expiration

        return new_tokens['access_token']


def get_google_access_token(request, redirect_uri):
    current_token = request.session['google_access_token']
    expiration = request.session['google_token_expires']
    now = int(time.time())
    if current_token and now < expiration:
        # Token still valid
        return current_token
    else:
        # Token expired
        refresh_token = request.session['google_refresh_token']
        new_tokens = get_google_token_from_refresh_token(refresh_token, redirect_uri)
        # Update session
        # expires_in is in seconds
        # Get current timestamp (seconds since Unix Epoch) and
        # add expires_in to get expiration time
        # Subtract 5 minutes to allow for clock differences
        expiration = int(time.time()) + new_tokens['expires_in'] - 300

        # Save the token in the session
        request.session['google_access_token'] = new_tokens['access_token']
        request.session['google_token_expires'] = expiration

        return new_tokens['access_token']

"""
Generic API for Office
"""


def make_office_api_call(method, url, token, user_email, payload=None, parameters=None):
    # Send these headers with all API calls
    headers = {
        'User-Agent': 'boarddirector',
                'Authorization': 'Bearer {0}'.format(token),
                'Accept': 'application/json',
                # This header makes office return "Mailbox info is stale", and it's not that obvious why is it used at all. Comment it out for the moment.
                # 'X-AnchorMailbox': user_email,
                'Prefer': 'outlook.timezone="{0}"'.format(timezone.get_current_timezone().zone)
        }

    # Use these headers to instrument calls. Makes it easier
    # to correlate requests and responses in case of problems
    # and is a recommended best practice.
    request_id = str(uuid.uuid4())
    instrumentation = {'client-request-id': request_id,
                       'return-client-request-id': 'true'}

    headers.update(instrumentation)

    if method.upper() == 'GET':
        response = requests.get(url, headers=headers, params=parameters)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, headers=headers, params=parameters)
    elif method.upper() == 'PATCH':
        headers.update({'Content-Type': 'application/json'})
        response = requests.patch(url, headers=headers, data=json.dumps(payload), params=parameters)
    elif method.upper() == 'POST':
        headers.update({'Content-Type': 'application/json'})
        response = requests.post(url, headers=headers, data=json.dumps(payload), params=parameters)
    else:
        raise ValueError("Illegal method " + method)

    logger.debug("%s %s Headers:\n%s" % (method, url, str(headers)))
    try:
        response.raise_for_status()
    except HTTPError as e:
        logger.error("Bad response from Office: %d: %s" % (response.status_code, response.text))
        raise e

    return response


"""
Get me
"""


def get_office_me(access_token):
    get_me_url = outlook_api_endpoint.format('/Me')

    # Use OData query parameters to control the results
    #  - Only return the DisplayName and EmailAddress fields
    query_parameters = {'$select': 'DisplayName,EmailAddress'}

    r = make_office_api_call('GET', get_me_url, access_token, "", parameters=query_parameters)

    # if r.status_code == requests.codes.ok:
    #     return r.json()
    # else:
    #     return "{0}: {1}".format(r.status_code, r.text)
    try:
        return r.json()
    except:
        return {'error': r.text}


def get_google_me(access_token):
    get_me_url = 'https://www.googleapis.com/oauth2/v1/userinfo'

    headers = {
        'User-Agent': 'boarddirector',
        'Authorization': 'Bearer {0}'.format(access_token),
        'Accept': 'application/json'
    }

    r = requests.get(get_me_url, headers=headers)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}

"""
Get/Create calendars for Office
"""


def get_office_calendars(access_token, user_email):
    get_cal_url = outlook_api_endpoint.format('/me/calendars')

    query_parameters = {}

    r = make_office_api_call('GET', get_cal_url, access_token, user_email, parameters=query_parameters)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}


def create_office_event(access_token, user_email, calendar_id, payload):
    url = outlook_api_endpoint.format('/me/calendars/' + calendar_id + '/events')
    r = make_office_api_call('POST', url, access_token, user_email, payload=payload)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}

"""
Get/Create calendars for Google
"""


def get_google_calendars(access_token):
    get_cal_url = 'https://www.googleapis.com/calendar/v3/users/me/calendarList'

    headers = {
        'User-Agent': 'boarddirector',
        'Authorization': 'Bearer {0}'.format(access_token),
        'Accept': 'application/json'
    }

    r = requests.get(get_cal_url, headers=headers)

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}


def create_google_event(access_token, calendar_id, payload):
    # url = 'https://www.googleapis.com/calendar/v3/calendars/'+ calendar_id +\
    #             '/events?maxAttendees=' + str(extra_members.count()) + '&sendNotifications=true'
    url = 'https://www.googleapis.com/calendar/v3/calendars/' + calendar_id + '/events?&sendNotifications=true'

    headers = {
        'User-Agent': 'boarddirector',
        'Authorization': 'Bearer {0}'.format(access_token),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    r = requests.post(url, headers=headers, data=json.dumps(payload))

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}


"""
Get events from google/office
"""


def get_google_events(access_token, calendar_id, params):
    """
    get google events
    """
    url = 'https://www.googleapis.com/calendar/v3/calendars/{0}/events'.format(calendar_id)
    headers = {
        'User-Agent': 'boarddirector',
        'Authorization': 'Bearer {0}'.format(access_token),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}


def get_office_events(access_token, user_email, calendar_id, params):
    url = 'https://outlook.office.com/api/v2.0/me/calendars/{0}/calendarview'.format(calendar_id)

    r = make_office_api_call('GET', url, access_token, user_email, parameters=params)
    r.raise_for_status()

    try:
        r.raise_for_status()
        return r.json()
    except:
        return {'error': r.text}
