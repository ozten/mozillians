from django.conf import settings
from django.contrib.auth.models import User, check_password

import ldap

import commonware.log

from larper import store_assertion, UserSession

log = commonware.log.getLogger('m.browserid')

log.debug("Loading browserid.backend")

class SaslBrowserIDBackend(object):
    """Authenticates the user's BrowserID assertion and our audience
    with the LDAP server via the SASL BROWSER-ID authentication
    mechanism."""
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, request=None, assertion=None):
        log.debug("authenticate called")
        #log.info("browserid authentication %s %s called!" % assertion)


        if request == None or assertion == None:
            return None

        store_assertion(request, assertion) # TODO this smells

        directory = UserSession(request)
        login_valid = False
        try:
            (registered, details) = directory.registered_user()
            log.info("Registered user? %s details=[%s]" % (str(registered), details))
            login_valid = registered
            if registered:
                log.info("Storing unique_id=%s into the session" % details)
                request.session['unique_id'] = details
            else:
                # TODO, use this on a browserid registration page
                request.session['verified_email'] = details
        except ldap.OTHER, o:
            # TODO... 
            store_assertion(request, None)
            # OTHER: {'info': 'SASL(-5): bad protocol / cancel: Browserid.org assertion verification failed.', 'desc': 'Other (e.g., implementation specific) error'}
            # such as stale assertion - timeout
            log.error(o)
        except Exception, e:
            store_assertion(request, None)
            log.error("Unknown error")
            log.error(e)

        if login_valid:
            try:
                person = directory.get_by_unique_id(details)
                log.debug("Checking for %s in the database" % person.username)
                user = User.objects.get(username=person.username)
            except User.DoesNotExist:
                # TODO aok - do we want this to happen from registration only?
                user = User(username=person.username,
                            first_name=person.first_name,
                            last_name = person.last_name,
                            email=person.username)
                user.set_unusable_password()
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.save()
                log.debug('Created new user in the db %s' % person.username)
            return user
        log.debug("browserid auth failing")
        return None

    def get_user(self, user_id):
        log.debug("Browserid backend get_user called... Searching for user based on %s" % user_id)
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            log.debug("No user found")
            return None
