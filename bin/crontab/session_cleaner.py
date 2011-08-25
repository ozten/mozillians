#!/usr/bin/env python
"""
BrowserID Session Cleaner
-------------------------

Run this cron periodically. Once per minute wouldn't be unreasonable.
Cron uses SESSION_EXP_SECONDS from settings.py or settings_local.py. 
It will delete all sessions that are N seconds older than now.

It is safe to run overlapping itself.

If this cron doesn't run, bad things will eventually happen such as:

* BrowserID authenication will be slow
* DB fill up
* Baby Narwhals will become Sashimi

"""
import os
import sys
import site

ROOT = os.path.dirname(      # bin
           os.path.dirname(  # crontab
               os.path.dirname(os.path.abspath(__file__))))
path = lambda *a: os.path.join(ROOT, *a)

# Adjust the python path and put local packages in front.
prev_sys_path = list(sys.path)

# Global (upstream) vendor library
site.addsitedir(path('vendor'))
site.addsitedir(path('vendor/lib/python'))

# Move the new items to the front of sys.path. (via virtualenv)
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path
sys.path.insert(0, path(''))

from django.core.management import setup_environ
try:
    import settings_local as settings
except ImportError:
    try:
        import settings
    except ImportError:
        import sys
        sys.stderr.write(
            "Error: Tried importing 'settings_local.py' and 'settings.py' "
            "but neither could be found (or they're throwing an ImportError)."
            " Please come back and try again later.")
        raise

setup_environ(settings)

from django.db import connection, transaction
cursor = connection.cursor()
delsql = """DELETE FROM browserid_session
            WHERE created < DATE_SUB(NOW(), INTERVAL %d SECOND)"""

cursor.execute("SELECT COUNT(digest) FROM browserid_session")
before = cursor.fetchone()[0]

# Django bug cursore.excute(delsql, [60]) throws
# AttributeError: 'Cursor' object has no attribute '_last_executed'
# value is from settings, so SQLInject risk is low
cursor.execute(delsql % settings.SESSION_EXP_SECONDS)

cursor.execute("SELECT COUNT(digest) FROM browserid_session")
after = cursor.fetchone()[0]

transaction.commit_unless_managed()
print "Session cleanup before=[%d] after=[%d] cleaned=[%d]" %\
    (before, after, before - after)
