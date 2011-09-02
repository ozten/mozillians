from django.shortcuts import redirect

from django.contrib import auth
from django_browserid.forms import BrowserIDForm

import ldap

import commonware.log

from larper import store_assertion, UserSession


log = commonware.log.getLogger('m.browserid')

# I think I need to write a backend auth package.
# Consider renaming this app to sasl-browserid
# Follow django-browserid's user creation 

# login should redirect to register and say "shout@ozten.com" is 
# an unknown account, would you like to create one?


def browserid_login(request):
    """We use contextprocessor, form, and ??? from django-browserid,
    but since the LDAP server does the BrowserID auth behind the
    scenes, we don't use it's auth code nor it's views."""
    form = BrowserIDForm(data=request.POST)
    if form.is_valid():
        log.debug("form looks good, doing authentication")
        assertion = form.cleaned_data['assertion']
        auth.logout(request)
        user = auth.authenticate(request=request, assertion=assertion)
        # DO we need a retry page?
        if user:
            log.debug("We got a user, logging in")
            auth.login(request, user)
            return redirect('profile', request.user.unique_id)
        log.debug("No user, authentication failed")
    else:
        log.debug("Form didn't validate %s" % str(request.POST))
    return redirect('register')

def browserid_register(request):
    """TODO registration w/o passwords"""
    pass
