from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.signals import user_logged_in

import commonware.log

import larper
from larper import UserSession

log = commonware.log.getLogger('m.browserid')

log.info("Setting up handle_login")

def handle_login(sender, **kwargs):
    request = kwargs['request']
    larper.store_password(request, request.POST.get('password', ''))
    if 'unique_id' in request.session:
        log.info("Setting unique_id=%s from session on user" % request.session['unique_id'])
        request.user.unique_id = request.session['unique_id']

user_logged_in.connect(handle_login)


class LarperMiddleware(object):
    """
    Responsible for populating the request.user object
    with the following attributes:
    * unique_id

    This complements the dn and password management from larper.dn and
    larper.password
    """
    def process_request(self, request):
        log.info("PROCESS REQUEST")
        if not hasattr(request, 'user'):
            msg = ('django.contrib.auth.middleware.AuthenticationMiddleware '
                   'is missing from your settings.py')
            raise ImproperlyConfigured(msg)

        if not hasattr(request, 'session'):
            msg = ('django.contrib.sessions.middleware.SessionMiddleware '
                   'is missing from your settings.py')
            raise ImproperlyConfigured(msg)

        if request.user.is_authenticated():
            _populate(request)
        else:
            log.debug("User is not authenticated!")

    def process_response(self, request, response):
        UserSession.disconnect(request)
        return response


def is_vouched(request):
    user = request.user

    def f():
        if not hasattr(user, 'person'):
            directory = UserSession.connect(request)
            user.person = directory.get_by_unique_id(user.unique_id)
        return bool(user.person.voucher_unique_id)
    return f


def _populate(request):
    user = request.user
    session = request.session

    if 'unique_id' in session:
        log.info("Setting unique_id=%s from session on user" % session['unique_id'])
        user.unique_id = session['unique_id']
    elif hasattr(user, 'ldap_user'):
        unique_id = user.ldap_user.attrs['uniqueIdentifier'][0]
        user.unique_id = session['unique_id'] = unique_id
        log.info("Setting unique_id=%s from ldap on user" % unique_id)
    else:
        log.info("NOT SETTING unique_id")
    user.is_vouched = is_vouched(request)
