#!/usr/bin/env python

from jToolkit.test import base_test_database

class TestMySQLADO(base_test_database.BaseTestDatabase):
    """Tests MySQL ADO (using the MySqlProv driver)"""
    def setup_class(cls):
        # Requires MySQL to be set up with a user "mytest", no password, with privileges on a database "mytest"
        class Config:
            pass
        config = Config()
        config.DBNAME = "mytest"
        config.DBHOST = None
        config.DBUSER = "mytest"
        config.DBPASSWORD = ""
        config.DBPROVIDER = "MySqlProv"
        config.DBTYPE = "mysql"
        base_test_database.BaseTestDatabase.create_database(config)

class TestMySQLADOWithHost(base_test_database.BaseTestDatabase):
    """Tests MySQL ADO (using the MySqlProv driver) with DBHOST defined.  This is broken at the moment"""
    def setup_class(cls):
        # Requires MySQL to be set up with a user "mytest", no password, with privileges on a database "mytest"
        class Config:
            pass
        config = Config()
        config.DBNAME = "mytest"
        config.DBHOST = "localhost"
        config.DBUSER = "mytest"
        config.DBPASSWORD = ""
        config.DBPROVIDER = "MySqlProv"
        config.DBTYPE = "mysql"
        base_test_database.BaseTestDatabase.create_database(config)

# At some point, we should also have a network test
