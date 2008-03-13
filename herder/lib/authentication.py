import logging

from authkit.users import UsersReadOnly
from authkit.permissions import RequestPermission, HasAuthKitRole

log = logging.getLogger(__name__)

class HasContextRole(RequestPermission):

    def __init__(self, role, all=False, keys=[], id_key=None):

        self.role = role
        self.all = all
        self.keys = keys
        self.id_key = id_key

    def check(self, app, environ, start_response):

        # start with the basic role passed in
        roles = [self.role]

        # get the routing information
        route_info = environ['pylons.routes_dict']

        # look for other roles that are the equivalent, in this context
        if self.id_key is not None and 'id' in route_info:
            roles.append('%s-%s-%s' % (self.id_key, route_info['id'], 
                                       self.role))

        for k in self.keys:
            if k in environ['pylons.routes_dict']:
                roles.append('%s-%s-%s' % (k, environ['pylons.routes_dict'][k], 
                                           self.role)
                             )

        # defer to the included permission checker
        return HasAuthKitRole(roles, all=self.all).check(
            app, environ, start_response)

