import logging

from authkit.authorize.pylons_adaptors import authorize
from authkit.permissions import HasAuthKitRole, ValidAuthKitUser

from tower.lib.base import *

log = logging.getLogger(__name__)

class AccountController(BaseController):

    @authorize(ValidAuthKitUser())
    def login(self):
        return render('/account/login_successful.html')

    def logout(self):
        return render('/account/logout.html')
