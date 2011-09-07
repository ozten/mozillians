========================
BrowserID and Mozillians
========================

How the ...
-----------

BrowserID is implemented partially in Django, partially in our 
LDAP directory, and by using a new LDAP plugin `sasl-browserid`. 
This allows us to maintain the LARPER security model.

.. image:: http://farm7.static.flickr.com/6067/6124318271_c7c0cee305_o.png
    :height: 356px
    :width: 600px
    :alt: Diagram of SASL BROWSER-ID plugin and Mozillians.org
    :target: http://www.flickr.com/photos/ozten/6124318271/

System Architecture
'''''''''''''''''''

Let's look at a typical authentication flow.

1. User clicks Sign-in button in HTML rendered from Django.

2. Browser requests an assertion from BrowserID.org.

3. Browser POSTs assertion to Django

4. Django code uses sasl_interactive_bind_s with BROWSER-ID as the auth mechanism. Assertion and audience are given as CB_USER and CB_AUTHNAME credentials.

5. SASL BROWSER-ID client plugin is loaded and sends a string:

  .. parsed-literal::

     assertion_value\0audience_value\0

6. SASL BROWSER-ID server plugin is loaded and parses inputs.

7. Server plugin uses `MySQL` queries based on the MD5 checksum of the assertion to see if the user already has an active session. It sees a cache miss.

8. Server plugin uses `Curl` to verify the assertion and audience with BrowserID.org.

9. Server plugin uses `YAJL` to parse the JSON response. It sees status set to "okay". It sees an email address.

10. Server plugin creates a session which contains a MD5 digest of the assertion, the user's email address, and the current timestamp.

11. Server plugin sets authid and authname to the user's email address.

12. `slapd` attempts to map the username into a valid DN. It uses the following configuration:

  .. parsed-literal::

      authz-regexp
        uid=([^,]*),cn=browser-id,cn=auth
        ldap:///ou=people,dc=mozillians,dc=org??one?(uid=$1)

Example: `slapd` has `dn:uid=shout@ozten.com,cn=browser-id,cn=auth` as the user's DN. It searches for uid=shout@ozten.com which matches one record. `slapd` then set's the user's identity to `uniqueIdentifier=32aef32b,dc=mozillians,dc=org`.

13. Server plugin returns a success status to the client.

14. Client returns a success status to Django.

15. Django uses `ldap_whoami_s` to determine the DN of the current user.

16. The DN *does not* contain `,cn=browser-id,cn=auth`, so Django treats this as a successful BrowserID login.

17. The `assertion` is stored securly in Django's session (via a signed cookie).

BrowserID Session
'''''''''''''''''''

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

The session table contains only a MD5 digest of assertions, email addresses, and timestamps.

The table *should not* be accessible to middleware and is only accessed from the Server side plugin, running on the slapd machines.

Current Session Flow
''''''''''''''''''''
Let's examine a similar flow, but for a user with a current session.

1. Browser sends session Cookie.

2. Django decrypts assertion and uses it with the audience in a sasl_interactive_bind_s. Steps 4 through 6 of original flow.

3. Server plugin checks for an active session using an MD5 digest of the assertion. It finds a session cache hit and retrieves the email address.

4. Server plugin updates the timestamp of this session.

5. Steps 11 through 17 happen just like our original flow, with the Server plugin setting the authid and authname to the user's email address.

Stale Session Flow
''''''''''''''''''''
This time our user's BrowserID Session has timedout.

1. Browser sends session Cookie.

2. Django decrypts assertion and uses it with the audience in a sasl_interactive_bind_s. Steps 4 through 6 of original flow.

3. Server plugin checks for an active session using an MD5 digest of the assertion. It sees a cache miss (Identical to step 7 in original flow).

4. Server plugin goes through steps 8 and 9, but this time the JSON response contains status set to "failure". This is because the assertion and audience inputs are no longer valid.

5. Server plugin returns a auth failure code.

6. Client returns an auth failure code.

7. Django code checks for failure. It clears the current session.

New User Flow
'''''''''''''

Considering our original flow, if at step 16 the DN *did* contain `,cn=browser-id,cn=auth`, the we would have a new user. The following captures that flow.

1. The email address is parsed out from the DN.

2. For compatiblity with django-auth-ldap as well as maintaining user analytics, basic information about the user are recorded in the Django MySQL database.

3. The user is logged in. The user's assertion is set into the Django session.

4. *TBD* - The email address is noted in the session as a new user. The user is sent to the registration path to complete their creation of a LDAP user account.

Libraries
'''''''''
We reuse the JS and Form from `django-browserid`_, but the backend and other 
bits don't match our requirements.

We use the `SASL BROWSER-ID`_ authentication mechanism via a plugin running
under OpenLDAP.

_`django-browserid`: https://github.com/mozilla/django-browserid
_`SASL BROWSER-ID`: https://github.com/ozten/sasl-browserid

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
