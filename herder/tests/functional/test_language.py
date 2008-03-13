from herder.tests import *

class TestLanguageController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='language'))
        # Test response...
