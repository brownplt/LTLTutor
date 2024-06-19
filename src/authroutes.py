
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
    login_manager.login_view = 'authroutes.login'

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
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            #return render_template('auth/login.html', error = 'Invalid username or password.')
            return redirect(url_for('authroutes.login'))
    elif request.method == 'GET':
        return render_template('auth/login.html')

@authroutes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('authroutes.login'))

@authroutes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        session = Session(bind=engine)

        # Check if a user with the given username already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('A user with that username already exists.')
            return render_template('auth/signup.html')

        password_hash = generate_password_hash(password)
        user = User(username=username, password_hash=password_hash)
        session.add(user)
        session.commit()

        # Now that the user is created, log them in
        login_user(user)
        session.close()
        return redirect(url_for('index'))
    return render_template('auth/signup.html')