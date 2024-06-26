
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session, sessionmaker, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri

from flask import Blueprint
import os
import random
import string
from functools import wraps

authroutes = Blueprint('authroutes', __name__)


def generate_random_string():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(6))
    return random_string

def gen_anon_user_name():
    return 'anon-user-' + generate_random_string()

Base = declarative_base()
engine = create_engine(get_db_uri())
Session = sessionmaker(bind=engine, expire_on_commit=True)

USER_TABLE = 'users'
COURSE_TABLE = 'registered_courses'


class Course(Base):
    __tablename__ = COURSE_TABLE
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    owner = Column(String)



class User(UserMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }


class AnonymousStudent(User):
    __mapper_args__ = {
        'polymorphic_identity': 'anonymous-student',
    }


class CourseStudent(User):
    __mapper_args__ = {
        'polymorphic_identity': 'course-student',
    }

    course_id: Mapped[str] = mapped_column(String, nullable=True) 


class CourseInstructor(User):
    __mapper_args__ = {
        'polymorphic_identity': 'course-instructor',
    }
    password_hash: Mapped[str] = mapped_column(String, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)





def login_required_as_courseinstructor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is not authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('login'))  # Assuming 'login' is the endpoint for your login page
        # Check if the user is not a CourseInstructor
        if not isinstance(current_user, CourseInstructor):
            abort(403)  # Forbidden access
        return f(*args, **kwargs)
    return decorated_function

Base.metadata.create_all(engine)

inspector = inspect(engine)
if USER_TABLE not in inspector.get_table_names():
    Base.metadata.tables[USER_TABLE].create(engine)


if COURSE_TABLE not in inspector.get_table_names():
    Base.metadata.tables[COURSE_TABLE].create(engine)

def init_app(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'authroutes.login'

    @login_manager.user_loader
    def load_user(user_id):
        with Session() as session:
            user = session.query(User).get(int(user_id))
            return user


@authroutes.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        user = None
        canLogin = False

        user_type = request.form.get('user_type')
        with Session() as session:
            if user_type == 'course-instructor':
                username = request.form.get('username')
                password = request.form.get('password')
                user = session.query(CourseInstructor).filter_by(username=username).first()

                canLogin = (user is not None) and check_password_hash(user.password_hash, password)

                if not canLogin:
                    flash('Invalid username or password.')
                    return redirect(url_for('authroutes.login'))

            elif user_type == 'course-student':
                username = request.form.get('username')
                course_id = request.form.get('course_id')
                user = session.query(CourseStudent).filter_by(username=username, course_id=course_id).first()

                ## If user did not already exist, create a new user
                if user is None:
                    # Create a new user
                    user = CourseStudent(username=username, course_id=course_id)
                    session.add(user)
                    session.commit()

                    canLogin = user is not None
            elif user_type == 'anonymous-student':
                username = gen_anon_user_name()
                user = AnonymousStudent(username=username)
                

                ## TODO: Check if user already exists, if so -- generate a new username

                session.add(user)
                session.commit()
                canLogin = user is not None
            else:
                return "Invalid user type.", 400

            if canLogin:
                print('Logging in user')
                login_user(user)
                return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('auth/login.html')
    else:
        return "Invalid request method.", 400

@authroutes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('authroutes.login'))

@authroutes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        with Session() as session:
            username = request.form.get('username')
            password = request.form.get('password')
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                flash(f'Username {username} is already taken. Please choose another one.')
                return render_template('auth/signup.html')

            password_hash = generate_password_hash(password)
            user = CourseInstructor(username=username, password_hash=password_hash)
            session.add(user)
            session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('auth/signup.html')


### New route to register exercises



## TODO: Change this to register course, and add it to instructor
@authroutes.route('/register-course', methods=['GET', 'POST'])
@login_required_as_courseinstructor
def register_exercise():
    if request.method == 'POST':    
        coursename = request.form.get('coursename')
        
        if not coursename or len(coursename) == 0:
            flash('Invalid course name.')
            return render_template('instructorhome.html')
        
        
        owner = current_user.username
        with Session() as session:

            # Check if a course with the same name already exists
            existing_course = session.query(Course).filter_by(name=coursename).first()
            if existing_course:
                flash(f'Course {coursename} already exists. Please choose another name.')
                return render_template('instructorhome.html')

            course = Course(name=coursename, owner=owner)
            session.add(course)
            session.commit()
            flash(f'Course {coursename} registered successfully.')
            return redirect(url_for('authroutes.register_exercise'))
    return render_template('instructorhome.html')


def retrieve_course_data(exercise_name) -> Course:
    with Session() as session:
        exercise = session.query(Course).filter_by(name=exercise_name).first()
        return exercise

def get_owned_courses(username):
    with Session() as session:
        exercises = session.query(Course).filter_by(owner=username).all()
        return exercises