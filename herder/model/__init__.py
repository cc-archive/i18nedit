from language import Language as DomainLanguage
from language import Language
from domain import Domain
from message import Message

from pylons import config
from sqlalchemy import Column, MetaData, Table, types
from sqlalchemy.orm import mapper
from sqlalchemy.orm import scoped_session, sessionmaker

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy import types

def setup_model(model, metadata, **p):
    pass

def init_model(bind):
    """Call me at the beginning of the application.
       'bind' is a SQLAlchemy engine or connection, as returned by
       sa.create_engine, sa.engine_from_config, or engine.connect().
    """
    global engine, ctx, Session
    engine = bind

    ctx = Session = orm.scoped_session(
        orm.sessionmaker(transactional=True, autoflush=True, bind=bind))

    #orm.mapper(Blog, blog_table,
    #    order_by=[blog_table.c.date.desc()])

meta = metadata = sa.MetaData()
