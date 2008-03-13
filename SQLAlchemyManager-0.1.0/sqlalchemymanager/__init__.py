"""\
SQLAlchemyManager - Provides a sensible way of using SQLAlchemy in WSGI applications 
"""

# SQLAlchemy Imports

from sqlalchemy.orm import sessionmaker
from sqlalchemy import engine_from_config, MetaData
from sqlalchemy import Table #, Column, types
from sqlalchemy.orm import mapper#, relation

class Model(dict):
    """\
    A dictionary like object where keys can also be accessed as attributes.
    """
    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

class SQLAlchemyManager(object):
    """\
    Really simple SQLAlchemy middleware
    which also helps in setting up the model and provides sensible access to 
    key SQLAlchmey objects
    """
    def __init__(self, app, app_conf, fns=[]):
        self.metadata = MetaData()
        self.model = Model()
        # We do this before anything else so that the setup fns don't
        # have access to most of the attributes
        for fn in fns:
            model_dict = fn(self.model, self.metadata)
            if isinstance(model_dict, dict):
                for k, v in model_dict:
                    if self.model.has_key(k):
                        raise Exception("The model already has an object named %s"%k)
                    self.model[k] = v
            elif model_dict is not None:
                raise Exception("Function %s returned %s, expected a dictionary or None"%(fn, model_dict))
        self.config = app_conf
        self.engine = engine_from_config(self.config, 'sqlalchemy.')
        self.session_maker = sessionmaker(
            autoflush=True, 
            transactional=True,
        )
        self.app = app

    # Don't think we need these
    def create_all(self):
        """\
        Create all the required tables
        """
        self.metadata.create_all(bind=self.engine)

    #def mapper(self, obj, table, *k, **p):
    #    self.model[table.name+'_mapper'] = mapper(obj, table, *k, **p)
    #    return self.model[table.name+'_mapper']

    #def object(self, obj):
    #    self.model[obj.__name__] = obj
    #    return self.model[obj.__name__]

    #def table(self, name, columns=[], name_in_model=None, **p):
    #    if name_in_model is None:
    #        name_in_model = name
    #    self.model[name_in_model] = Table(
    #        name,
    #        self.metadata,
    #        *columns,
    #        **p
    #    )
    #    return self.model[name_in_model]

    
    def __call__(self, environ, start_response):
        connection = self.engine.connect()
        session = self.session_maker(bind=connection)
        environ['sqlalchemy.manager'] = self
        environ['sqlalchemy.model'] = self.model
        environ['sqlalchemy.session'] = session
        try:
            return self.app(environ, start_response)
        finally:
            session.close()
            connection.close()

if __name__ == '__main__':

    from sqlalchemy import Table, Column, types
    from sqlalchemy.sql import select

    def setup_model(model, metadata, **p):
        model.table1 = Table("table1", metadata,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.String, nullable=False),
        )
        class MyClass(object):
            pass
        model.MyClass = MyClass
        model.table1_mapper = mapper(model.MyClass, model.table1)

    def app(environ, start_response):
        # The model is the same across requests so is safe to save as a global
        # somewhere in your application.
        model = environ['sqlalchemy.model']
        # You will get a new session object on each request so you shouldn't save it
        session = environ['sqlalchemy.session']
   
        # Create the tables
        environ['sqlalchemy.manager'].create_all()

        # Use the SQLExpression API via the session object
        select_statement = select([model.table1])
        select_result = [row for row in session.execute(select_statement)]
        
        # Or use the ORM API
        mr_jones = model.MyClass()
        mr_jones.name = 'Mr Jones'
        session.save(mr_jones)
        session.commit()
        multiple_mr_jones = session.query(model.MyClass).filter(model.MyClass.name=='Mr Jones').order_by(model.table1.c.name).all()
        
        # Return the data
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [
            '''
    Select Result: 
    %s
    
    Mr Jones Results:
    %s 
            '''%(
                select_result,
                ', '.join([person.name for person in multiple_mr_jones])
            )
        ]

    app_conf = {
        'sqlalchemy.url':'sqlite:///test.db',
        'sqlalchemy.echo':'false', # Change to true to see the SQL generated
    }

    app = SQLAlchemyManager(app, app_conf, [setup_model])

    # Set up some fake WSGI objects for printing the putput
    def printing_start_response(status, headers, exc_info=None):
        print "Status: %s"%status
        print "Headers: %s"%headers
        print "Exc_info: %s"%exc_info
        print

    fake_environ = {}
    
    # Test the app and middleware using the fake WSGI objects to print
    # the output.
    for output in app(fake_environ, printing_start_response):
        print output

