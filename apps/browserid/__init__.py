import sys

import ldap

from ldap.sasl import sasl, CB_USER, CB_AUTHNAME

class credentials(sasl):
    """This class handles SASL BROWSER-ID authentication."""

    def __init__(self, assertion, audience):
        auth_dict = {CB_USER:assertion,
                     CB_AUTHNAME: audience}
        sasl.__init__(self, auth_dict, 'BROWSER-ID')

    #def callback(self,cb_id,challenge,prompt,defresult):
    #    print("id=%d, challenge=%s, prompt=%s, defresult=%s" % (cb_id,challenge,prompt,defresult))
    #    return sasl.callback(self,cb_id,challenge,prompt,defresult)
