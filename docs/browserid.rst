========================
BrowserID and Mozillians
========================

How the ...
-----------

BrowserID is implemented partially in Django and partially in our 
LDAP directory. This allows us to maintain the LARPER security model.

We authenticate the user via BrowserID which gives us an email address.
This will either be a valid email address in the system or will be
an unknown email address. We maintain a 6 hour session during which
we do not re-authenticate the user. This session is managed outside
of Django via a crontab. The crontab lives under bin/crontab/ for 
developer convience, but in stage and production is a seperate component.

Development Mode:

    bin/crontab/session_cleaner.py --django

Production Mode:

    bin/crontab/session_cleaner.py

In production mode, the cron will read from session_cleaner_conf.py

Libraries
'''''''''
We reuse the JS and Form from django-browserid, but the backend and other 
bits don't match our requirements.

We use the SASL BROWSER-ID_ authentication mechanism via a plugin running
under OpenLDAP.

_SASL BROWSER-ID: http://github.com/ozten/sasl-browserid

STATUS
------

The BrowserID integration is functional enough for a demo and the hard bits
are complete for a production ready system... with the following caveauts:

Session State
'''''''''''''
We have to store the user's browserid assertion in a per-user
store. For the demo, we're using the secure session which is 
cookie based. After some of thought, this is probably the best
place, even though it increases the size of the cookie...

The assertion is effectively a password, since it is used by 
SASL BROWSER-ID if it is found in a session cache.

To secure this backend session, Django shouldn't know about the MySQL
which hosts the table browserid_session.

UX and Flow
'''''''''''
Login and Legacy login work. The overall UX needs some work.

Registration - there is a hook to store the email address of an authenticated
but unknown user in the session, so that a registration flow could use it.
It is not hooked up.

It's not clear what the best registration flow is. Do we support legacy
registration as well as BrowserID based registration?

Change Password - Should this appear on edit profile? When?
