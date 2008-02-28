import logging

from tower.lib.base import *

log = logging.getLogger(__name__)

class AuthController(BaseController):

    def signout(self):
        return render('/signout.html')
