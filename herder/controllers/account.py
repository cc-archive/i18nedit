import logging

from authkit.authorize.pylons_adaptors import authorize
from authkit.permissions import HasAuthKitRole, ValidAuthKitUser

from herder.lib.base import *

log = logging.getLogger(__name__)

class AccountController(BaseController):

    @authorize(ValidAuthKitUser())
    @with_user_info
    def login(self):

        return render('/account/login_successful.html')

    def logout(self):

        # make sure the logged-in portions of the UI don't show
        # c.remote_user = False

        return render('/account/logout.html')

    def register(self):

        return render('/account/registration/index.html')

    def confirm(self):

        # get the hash from the query string
        # reg_hash = ...

        # check the registration
        registration = model.UserRegistration.exists(reg_hash)
        if registration:

            # registration valid
            model.users.user_create(registration.username, 
                                    password=registration.password, 
                                    group="Users")

            return render('/account/registration/success.html')

        else:
            return render('/account/registration/invalid.html')

    @authorize(ValidAuthKitUser())
    @with_user_info
    def profile(self):

        return render('/account/profile.html')
