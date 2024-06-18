from app import app

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri


## TODO: Is this too fragile? Should we create the table even if the bind is not None?
Base = declarative_base()

USER_TABLE = 'users'
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



# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define the load_user callback function
@login_manager.user_loader
def load_user(user_id):
    session = Session(bind=engine)
    user = session.query(User).get(user_id)
    session.close()
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        session = Session(bind=engine)
        user = session.query(User).filter_by(username=username).first()
        session.close()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)
        user = User(username=username, password=password_hash)
        session = Session(bind=engine)
        session.add(user)
        session.commit()
        session.close()
        flash('Account created successfully.')
        return redirect(url_for('login'))
    return render_template('signup.html')