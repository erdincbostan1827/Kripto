from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
def make_engine(url='sqlite+pysqlite:///:memory:',**kwargs): return create_engine(url,future=True,**kwargs)
def init_db(engine): Base.metadata.create_all(engine)
def session_factory(engine): return sessionmaker(engine,expire_on_commit=False)
