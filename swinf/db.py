"""
define some wrapper for orms.
"""
__all__ = [
    "create_sqla", ]

from sqlalchemy.orm import scoped_session, sessionmaker
import swinf
from swinf import handler_hooks
from swinf.core.middleware import HandlerHookAdapter

class SqlaOrm(HandlerHookAdapter):
    """
    Hook Sqlalchemy orm to handler_hooks

    Sqlalchemy session will be loaded for every single request in a thread-safe environment.
    """
    def __init__(self, engine, hookto=None):
        self.engine = engine
        if hookto != None:
            hookto.add_processor('sqlalchemy_orm', self)

    def hook_start(self):
        swinf.ctx.orm = scoped_session(sessionmaker(bind=self.engine))

    def hook_end(self):
        swinf.ctx.orm.commit()

def create_sqla(engine):
    return SqlaOrm(engine, hookto=handler_hooks)
