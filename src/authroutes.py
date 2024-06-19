
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri

from flask import Blueprint
authroutes = Blueprint('authroutes', __name__)


Base = declarative_base()
engine = create_engine(get_db_uri())
Session = sessionmaker(bind=engine)

USER_TABLE = 'users'
class User(UserMixin, Base):
    __tablename__ = USER_TABLE

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)





Base.metadata.create_all(engine)

inspector = inspect(engine)
if USER_TABLE not in inspector.get_table_names():
        Base.metadata.tables[USER_TABLE].create(engine)

# Define the load_user callback function
# @current_app.login_manager.user_loader
# def load_user(user_id):
#     session = Session(bind=engine)
#     user = session.query(User).get(user_id)
#     session.close()
#     return user



def init_app(app):
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        session = Session()
        user = session.query(User).get(int(user_id))
        session.close()
        return user


@authroutes.route('/login', methods=['GET', 'POST'])
def login():
    print('Login route with method: ' + request.method)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        session = Session(bind=engine)
        user = session.query(User).filter_by(username=username).first()
        session.close()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            print('Logged in successfully.')
            return render_template('index.html')
        else:
            print('Invalid username or password.')
            return render_template('auth/login.html', error = 'Invalid username or password.')
    elif request.method == 'GET':
        return render_template('auth/login.html')

@authroutes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@authroutes.route('/signup', methods=['GET', 'POST'])
def signup():
    ## Currently does not gracefully allow for multiple users with the same username
    ## Crashes application if username already exists
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)
        user = User(username=username, password_hash=password_hash)
        session = Session(bind=engine)
        session.add(user)
        session.commit()
        session.close()
        flash('Account created successfully.')
        return render_template('auth/login.html')
    return render_template('auth/signup.html')