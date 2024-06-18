



from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri
Base = declarative_base()

USER_TABLE = 'users'


## TODO: Is this too fragile? Should we create the table even if the bind is not None?
if Base.metadata.bind is None:
    engine  = create_engine(get_db_uri())
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
else:
    engine = Base.metadata.bind
inspector = inspect(engine)
if USER_TABLE not in inspector.get_table_names():
        Base.metadata.tables[USER_TABLE].create(engine)


class User(UserMixin, Base):
    __tablename__ = USER_TABLE

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)