from rest_framework.views import exception_handler

WRONG_REQUEST = 'Wrong request. Check full response json for details.'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        if 'detail' not in response.data:
            if response.status_code == 400:
                response.data['detail'] = WRONG_REQUEST

    return response
