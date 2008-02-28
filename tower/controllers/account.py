import logging

from tower.lib.base import *

log = logging.getLogger(__name__)

class AccountController(BaseController):

    def logout(self):
        return render('/account/logout.html')
