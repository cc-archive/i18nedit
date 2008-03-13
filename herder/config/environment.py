"""Pylons environment configuration"""
import os
import logging

from pylons import config
import sqlalchemy as sa
from sqlalchemy import engine_from_config

from sqlalchemymanager import SQLAlchemyManager
import authkit.users.sqlalchemy_04_driver

import herder.lib.app_globals as app_globals
import herder.lib.helpers
from herder.config.routing import make_map
from herder import model

log = logging.getLogger(__name__)

CONTEXT_ROLES = ('administer', 'translate', )

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """

    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='herder',
                    template_engine='mako', paths=paths)

    config['routes.map'] = make_map()
    config['pylons.g'] = app_globals.Globals()
    config['pylons.h'] = herder.lib.helpers

    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    config['pylons.g'].sa_engine = engine = \
        sa.engine_from_config(config, "sqlalchemy.")
    model.init_model(engine)

    # Sync up roles
    manager = SQLAlchemyManager(None, config, 
        [model.setup_model, authkit.users.sqlalchemy_04_driver.setup_model])
    manager.create_all()

    connection = manager.engine.connect()
    session = manager.session_maker(bind=connection)
    try:
        environ = {}
        environ['sqlalchemy.session'] = session
        environ['sqlalchemy.model'] = manager.model
        users = authkit.users.sqlalchemy_04_driver.UsersFromDatabase(environ)

        # sync up the roles for each domain and language
        for domain in model.Domain.all():

            for cr in CONTEXT_ROLES:

                if not users.role_exists('domain-%s-%s' % (domain.name, cr)):
                    users.role_create('domain-%s-%s' % (domain.name, cr))

            for lang in domain.languages:

                for cr in CONTEXT_ROLES:

                    if not users.role_exists('lang-%s-%s' % (lang.name, cr)):
                        users.role_create('lang-%s-%s' % (lang.name, cr))

        # commit the user setup work
        session.flush()
        session.commit()

    finally:
        session.close()
        connection.close()


