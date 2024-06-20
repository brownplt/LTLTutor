
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri

from flask import Blueprint
import os
import random
import string
authroutes = Blueprint('authroutes', __name__)


def generate_random_string():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(6))
    return random_string

Base = declarative_base()
engine = create_engine(get_db_uri())
Session = sessionmaker(bind=engine)

USER_TABLE = 'users'
EXERCISE_TABLE = 'registered_exercises'


class User(UserMixin, Base):
    __tablename__ = USER_TABLE

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AuthoredExercise(Base):
    __tablename__ = EXERCISE_TABLE

    id = Column(Integer, primary_key=True)
    exercise_data = Column(String)
    name = Column(String)
    owner = Column(String)



Base.metadata.create_all(engine)

inspector = inspect(engine)
if USER_TABLE not in inspector.get_table_names():
    Base.metadata.tables[USER_TABLE].create(engine)


if EXERCISE_TABLE not in inspector.get_table_names():
    Base.metadata.tables[EXERCISE_TABLE].create(engine)

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
            flash(f'Username {username} is already taken. Please choose another one.')
            
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


### New route to register exercises
@authroutes.route('/register-exercise', methods=['GET', 'POST'])
@login_required
def register_exercise():
    if request.method == 'POST':    
        json_files = [file for file in request.files.values() if file.filename.endswith('.json')]
        if not json_files or len(json_files) == 0:
            flash('Exercises must be uploaded as JSON files.')
            return render_template('auth/register-exercise.html')
        
        owner = current_user.username
        session = Session(bind=engine)
        for file in json_files:
            
            rand_postfix = "-" + generate_random_string()
            exercisename = file.filename.replace('.json', rand_postfix)
            contents = file.read().decode('utf-8')

            exercise = AuthoredExercise(exercise_data=contents, name=exercisename, owner=owner)
            session.add(exercise)
            session.commit()
            flash(f'Exercise {exercisename} registered successfully.')
        session.close()
        return redirect(url_for('authroutes.register-exercise'))
    return render_template('auth/register-exercise.html')


def retrieve_exercise(exercise_name) -> AuthoredExercise:
    session = Session(bind=engine)
    exercise = session.query(AuthoredExercise).filter_by(name=exercise_name).first()
    session.close()
    return exercise

def get_authored_exercises(username):

    session = Session(bind=engine)
    exercises = session.query(AuthoredExercise).filter_by(owner=username).all()
    session.close()
    return exercises