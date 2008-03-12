"""Setup the tower application"""
import logging

from paste.deploy import appconfig
from pylons import config

from sqlalchemymanager import SQLAlchemyManager
import authkit.users.sqlalchemy_04_driver

from tower.config.environment import load_environment, CONTEXT_ROLES
from tower.model import setup_model

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup tower here"""
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

    """
    # Populate the DB on 'paster setup-app'
    import tower.model as model
    users = UsersFromDatabase(model) 

    log.info("Setting up database connectivity...")
    engine = config['pylons.g'].sa_engine
    log.info("Creating tables...")
    model.metadata.create_all(bind=engine)
    log.info("Successfully set up.")
    
    #uri = conf['sqlalchemy.dburi'] 
    #engine = create_engine(uri) 
    ##print "Connecting to database %s" % uri 

    #model.meta.connect(engine) 
    #print "Creating tables" 
    #model.meta.create_all(engine) 
    print "Adding users and roles" 
    users.role_create("delete") 
    users.user_create("admin", password="opensesame") 
    users.user_add_role("admin", role="delete")

    log.info("Adding front page data...")
    page = model.Page()
    page.title = 'FrontPage'
    page.content = 'Welcome to the QuickWiki front page.'
    #model.Session.save(page)
    model.Session.commit()
    log.info("Successfully set up.")
    """

