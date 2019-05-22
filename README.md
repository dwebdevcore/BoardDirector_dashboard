# boarddirector.co #

## Development setup

### Vagrant 
Project has `Vagrantfile` to speed up development setup. So easiest way is:

- Install Vagrant
- run `vagrant up` inside project

### Gulp
Gulp is used to compile SASS files into CSS.

#### Setup:

- Install latest Node.js locally
- `npm install -g gulp`
- `cd apps/common/static`
- `npm install`

### Use:

From host machine (i.e. not Vagrant box):
- `start-gulp.cmd` in root (create & test similar for Linux environment)
- or `cd apps/common/static; gulp`

BTW, it'll start BrowserSync on :3000 port with proxying to Django. This way styles are refreshed without reload, 
also Django templates are watched and page is refreshed upon change. 

### Deployment:

- No special steps required: generated css files are stored in css.generated and committed into git.
- no minification yet in gulp (there is some in compress, I think).
- .map files are currently not committed, use locally for development.


### Notes on Bootstrap:

Project mostly uses outdated hand-made css layouts, with a lot of things messing up in all.css + custom.css.

To switch page to newer styles replace base styles:
```
{% block base_resources %}
  <link rel="stylesheet" href="{% static 'css.generated/base.css' %}"/>
  <script src="{% static 'js/libs/jquery-1.12.4/jquery.min.js' %}"></script>
{% endblock %}
```

This way you'll have:
- Bootstrap (so default `.row`/`.col.*.*`/`btn`, etc)
- Use single per-page stylesheet (possibly split into partials via SASS) so that it's under control
- Use common variables via SASS for colors, margins, etc


### REST Development:

Some highlights:

- `api_urls` is place to link Routers for each module, reason: to load it separately from `urls` modules and their dependencies. 
  Not strictly required, might be changed if needed
- `api_views` modules used to store viewsets and other things
- `/{account_url}/api/v1/` is binding point for all apis
- `/api/v1/` is binding point for "global" apis like `accounts/*`
- `common.api_urls` single router is constructed here, uniting routers from different apps  
- currently mapping is done without any app prefixes, there was no other good way to have single entrypoint 
  to list all available APIs from different apps (Yuri), if you know better way - you're welcome to fix it.
- there is a couple of useful mixins in `common.mixin` like 
  - `GetMembershipWithURLFallbackMixin` (used to get_membership and account without session requirement)
  - `PerActionSerializerModelViewSetMixin` (to have different serializers for different verbs, for less detailed list for example)
- and also `permissions.rest_permissions` with some common permission classes

### REST Usage:

Auth:

* Token Auth:
    * `POST /api/v1/token-auth/` body: `{"username": "user@email.com", "password": "password-here"}`
    * Store `token` field from response
    * Then add `Authorization: Token $token$` header to any subsequent request, this will authorize as user
    * Token may expire some time in future (currently no) in this case extra login is required

## Versions ##

### 0.1.0 (29-Oct-2015) ###
Based on the software as it wat migrated to Bitbucket repo on 30-Sep-2015. Adds the following changes:

* Make system robust for missing avatar / profile pictures. Just show the default picture when no picture can be read.
* Fix problem with calendar date localization
* Fabric deployment automation: functions to support configurtion and control of Supervisor, uWSGI and nginx services.

### 0.1.1 (02-Nov-2015) ###
Changes to Fabric deployment automation:

* support for side-by-side deployment of releases; functions to deploy, remove and activate releases.
* support for forward and backward database migrations.

### 0.2.0 (20-Nov-2015) ###
Feature: RSVP:

* added widget to set RSVP response / view current response.
* added table with RSVP per invitee in the meeting organiser's view.
* added expandable div with RSVP response history per invitee.

Changes to Fabric deployment automation:

* improve robustness in handling changes (add 'collectstatic' to deploy function and PIP update to activation function).
* cleanup obsolete code.

### 0.2.1 (23-Nov-2015) ###
Bugfix: board names may contain spaces and HTML escapes

### 0.2.2 (24-Nov-2015) ###
Bugfix: User.get_short_name() and User.get_full_name() to return names rather than parts of the e-mail address. 

### 0.2.3 (29-Feb-2016) ###
Bugfix:

* Problem with croppy, JSON fields and PostgreSQL is now programatically patched

Feature: configurable pricing

* added 2016 plans
* made "pricing" and "change plan" pages render dynamically based on available plans

### 0.3.0 (12-Apr-2016) ###

Feature: PDF viewer

### 0.3.1 (19-Jul-2016) ###

Bugfix: new settings for outgoing e-mails

### 0.3.2 (26-Jul-2016) ###

AddedHotjar site analytics script


### 15-Nov-2016 ###
 * Fixed tests
 * Added customer.io integration

### 30-Nov-2016 ###
 * Lockdown delete and share

## New Deployment Process ##
Documented in confluence [page](http://52.53.222.198:8090/display/WEB/Production+Deployment+process).


## OLD deployment process ##

* Open a terminal
* Activate the boarddirector dev virtualenv
* Navigate to the root directory of the boarddirector project
* type: `$ fab deploy:<version>`
* type: `$ fab activate:<version>`

(where <version> is the release tag to be deployed/activated)