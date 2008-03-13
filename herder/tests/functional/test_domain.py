from herder.tests import *

class TestDomainController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='domain'))
        # Test response...
