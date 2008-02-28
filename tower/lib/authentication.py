from tower.lib import jToolkit
from tower.lib.jToolkit import prefs
from authkit.users import UsersReadOnly

class PootleUsers(UsersReadOnly):

    def __init__(self, data, encrypt=None):
        super(PootleUsers, self).__init__(data, encrypt)

        self._prefs_file = data

    @property
    def _prefs(self):
        """Return the parsed prefs object."""
    
        return prefs.PrefsParser(self._prefs_file)

    def user_exists(self, username):
        
        return self._prefs.hasvalue(username)

    def role_exists(self, role):

        return False
        pass

    def group_exists(self, role):

        return False
        pass

    def user_password(self, username):

        return self._prefs.getvalue('%s.passwdhash' % username)

    """
    def user_group(self, username):
        pass

    def user_roles(self, username):
        pass

    """
