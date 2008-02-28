import logging
import tower.model
from tower.lib.base import *

log = logging.getLogger(__name__)

class DomainController(BaseController):

    def list(self):
        """Return a list of available translation domains."""

        c.domains = tower.model.Domain.all()
        return render('/domain/list.html')

    def view(self, id):
        """View a specific domain."""

        c.domain = tower.model.Domain.by_name(id)
        c.languages = c.domain.languages
        c.languages.sort()

        return render('/domain/view.html')

