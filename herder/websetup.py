"""Setup the herder application"""
import logging

from paste.deploy import appconfig
from pylons import config

from sqlalchemymanager import SQLAlchemyManager
import authkit.users.sqlalchemy_04_driver

from herder.config.environment import load_environment, CONTEXT_ROLES
from herder.model import setup_model

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup herder here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)

    manager = SQLAlchemyManager(None, conf.local_conf, 
        [setup_model, authkit.users.sqlalchemy_04_driver.setup_model])
    manager.create_all()

    connection = manager.engine.connect()
    session = manager.session_maker(bind=connection)
    try:
        environ = {}
        environ['sqlalchemy.session'] = session
        environ['sqlalchemy.model'] = manager.model
        users = authkit.users.sqlalchemy_04_driver.UsersFromDatabase(environ)

        # create default groups
        users.group_create("Users")

        # create default roles
        for role in CONTEXT_ROLES:
            users.role_create(role)

        # create the default administrative user
        users.user_create("admin", password="acbd18db4cc2f85cedef654fccc4a4d8")
        for role in CONTEXT_ROLES:
            users.user_add_role('admin', role)

        # commit the user setup work
        session.flush()
        session.commit()
    finally:
        session.close()
        connection.close()

