from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session, sessionmaker, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri

from flask import Blueprint, abort
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
INSTRUCTOR_EXERCISE_TABLE = 'instructor_exercises'


class Course(Base):
    __tablename__ = COURSE_TABLE
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    owner = Column(String)


class InstructorExercise(Base):
    """Stores exercises created by instructors"""
    __tablename__ = INSTRUCTOR_EXERCISE_TABLE
    id = Column(Integer, primary_key=True)
    name = Column(String)  # Human-readable name
    owner = Column(String)  # Username of instructor who created it
    course = Column(String, nullable=True)  # Optional: assigned to a specific course
    exercise_json = Column(String)  # JSON string of the exercise questions
    created_at = Column(String)  # ISO timestamp
    updated_at = Column(String)  # ISO timestamp



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
            return redirect(url_for('authroutes.login'))  
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

if INSTRUCTOR_EXERCISE_TABLE not in inspector.get_table_names():
    Base.metadata.tables[INSTRUCTOR_EXERCISE_TABLE].create(engine)

def init_app(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'authroutes.login'
    login_manager.login_message = ''

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




                ## TODO: User cannot be in more than one course. May have to change this later.


                ## Ensure that course_id exists
                course = session.query(Course).filter_by(name=course_id).first()
                if course is None:
                    flash('Could not find a course with ID ' + course_id)
                    return redirect(url_for('authroutes.login'))

                canLogin = user is not None
                ## If user did not already exist, create a new user
                if user is None:
                    # Create a new user
                    user = CourseStudent(username=username, course_id=course_id)
                    try:
                        session.add(user)
                        session.commit()
                        canLogin = user is not None
                    except Exception as e:
                        flash('User {username} already exists.'.format(username=username))
                        session.rollback()
                        canLogin = False
                        
                
            elif user_type == 'anonymous-student':
                ## This should really never happen, but just in case
                tries_remaining = 10
                username = ""
                while tries_remaining > 0:
                    username = gen_anon_user_name()
                    existing_user = session.query(User).filter_by(username=username).first()
                    if existing_user is None:
                        break
                    tries_remaining -= 1               

                user = AnonymousStudent(username=username)
                session.add(user)
                session.commit()
                canLogin = tries_remaining > 0
            else:
                return "Invalid user type.", 400

            if canLogin:
                print('Logging in user')
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Login failed. Please try again.')
                return redirect(url_for('authroutes.login'))
    elif request.method == 'GET':
        user_type = request.args.get('user_type', '')
        course_id = request.args.get('course_id', '')
        return render_template('auth/login.html', user_type=user_type, course_id=course_id)
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
            confirm_password = request.form.get('confirm_password')  # <-- Get confirm_password

            # Check if passwords match
            if password != confirm_password:
                flash('Passwords do not match. Please try again.')
                return render_template('auth/signup.html')

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

            login_link = url_for('authroutes.login', user_type='course-student', course_id=course.name, _external=True)

            flash(f'Course <code>{coursename}</code> registered successfully. <br><br> You can share it with students via the course code <code>{course.name}</code> or the link <code>{login_link}</code> <br><br>This link will also be available in your instructor dashboard.')
            return redirect(url_for('authroutes.register_exercise'))
    return render_template('instructorhome.html')


def retrieve_course_data(course_name) -> Course:
    with Session() as session:
        exercise = session.query(Course).filter_by(name=course_name).first()
        return exercise

def get_owned_courses(username):
    with Session() as session:
        exercises = session.query(Course).filter_by(owner=username).all()
        return exercises
    

## TODO: Only works if exactly one course per user.
# May have to change.
def getUserCourse(username):
    with Session() as session:
        course = session.query(CourseStudent).filter_by(username=username).first()

        if course is None:
            return ""

        return course.course_id


# =====================================================
# Instructor Exercise Management Routes
# =====================================================

def get_instructor_exercises(username):
    """Get all exercises created by an instructor"""
    with Session() as session:
        exercises = session.query(InstructorExercise).filter_by(owner=username).all()
        return exercises


def get_instructor_exercise_by_id(exercise_id):
    """Get a specific exercise by ID"""
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        return exercise


def get_exercises_for_course(course_name):
    """Get all exercises assigned to a specific course"""
    with Session() as session:
        exercises = session.query(InstructorExercise).filter_by(course=course_name).all()
        return exercises


@authroutes.route('/instructor/exercises', methods=['GET'])
@login_required_as_courseinstructor
def list_instructor_exercises():
    """List all exercises created by the instructor"""
    username = current_user.username
    exercises = get_instructor_exercises(username)
    owned_courses = get_owned_courses(username)
    course_names = [c.name for c in owned_courses]
    return render_template('instructor/exercises.html', 
                           exercises=exercises, 
                           course_names=course_names)


@authroutes.route('/instructor/exercises/new', methods=['GET', 'POST'])
@login_required_as_courseinstructor
def create_instructor_exercise():
    """Create a new exercise"""
    import json
    from datetime import datetime
    
    if request.method == 'POST':
        exercise_name = request.form.get('exercise_name', '').strip()
        exercise_json = request.form.get('exercise_json', '[]')
        course = request.form.get('course', None)
        
        if not exercise_name:
            flash('Exercise name is required.')
            return redirect(url_for('authroutes.create_instructor_exercise'))
        
        # Validate JSON
        try:
            questions = json.loads(exercise_json)
            if not isinstance(questions, list):
                raise ValueError("Exercise must be a list of questions")
        except (json.JSONDecodeError, ValueError) as e:
            flash(f'Invalid exercise JSON: {str(e)}')
            return redirect(url_for('authroutes.create_instructor_exercise'))
        
        now = datetime.utcnow().isoformat()
        
        with Session() as session:
            exercise = InstructorExercise(
                name=exercise_name,
                owner=current_user.username,
                course=course if course else None,
                exercise_json=exercise_json,
                created_at=now,
                updated_at=now
            )
            session.add(exercise)
            session.commit()
            exercise_id = exercise.id
        
        flash(f'Exercise "{exercise_name}" created successfully!')
        return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
    
    # GET request - show the exercise builder
    owned_courses = get_owned_courses(current_user.username)
    course_names = [c.name for c in owned_courses]
    return render_template('instructor/exercise_builder.html', 
                           exercise=None,
                           course_names=course_names)


@authroutes.route('/instructor/exercises/<int:exercise_id>', methods=['GET', 'POST'])
@login_required_as_courseinstructor
def edit_instructor_exercise(exercise_id):
    """Edit an existing exercise"""
    import json
    from datetime import datetime
    
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        
        if not exercise:
            flash('Exercise not found.')
            return redirect(url_for('authroutes.list_instructor_exercises'))
        
        if exercise.owner != current_user.username:
            flash('You do not have permission to edit this exercise.')
            return redirect(url_for('authroutes.list_instructor_exercises'))
        
        if request.method == 'POST':
            exercise_name = request.form.get('exercise_name', '').strip()
            exercise_json = request.form.get('exercise_json', '[]')
            course = request.form.get('course', None)
            
            if not exercise_name:
                flash('Exercise name is required.')
                return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
            
            # Validate JSON
            try:
                questions = json.loads(exercise_json)
                if not isinstance(questions, list):
                    raise ValueError("Exercise must be a list of questions")
            except (json.JSONDecodeError, ValueError) as e:
                flash(f'Invalid exercise JSON: {str(e)}')
                return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
            
            exercise.name = exercise_name
            exercise.exercise_json = exercise_json
            exercise.course = course if course else None
            exercise.updated_at = datetime.utcnow().isoformat()
            session.commit()
            
            flash(f'Exercise "{exercise_name}" updated successfully!')
            return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
        
        # GET request
        owned_courses = get_owned_courses(current_user.username)
        course_names = [c.name for c in owned_courses]
        
        # Make a copy of the exercise data to pass to the template
        exercise_data = {
            'id': exercise.id,
            'name': exercise.name,
            'course': exercise.course,
            'exercise_json': exercise.exercise_json,
            'created_at': exercise.created_at,
            'updated_at': exercise.updated_at
        }
        
    return render_template('instructor/exercise_builder.html', 
                           exercise=exercise_data,
                           course_names=course_names)


@authroutes.route('/instructor/exercises/<int:exercise_id>/delete', methods=['POST'])
@login_required_as_courseinstructor
def delete_instructor_exercise(exercise_id):
    """Delete an exercise"""
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        
        if not exercise:
            flash('Exercise not found.')
            return redirect(url_for('authroutes.list_instructor_exercises'))
        
        if exercise.owner != current_user.username:
            flash('You do not have permission to delete this exercise.')
            return redirect(url_for('authroutes.list_instructor_exercises'))
        
        exercise_name = exercise.name
        session.delete(exercise)
        session.commit()
        
        flash(f'Exercise "{exercise_name}" deleted.')
    
    return redirect(url_for('authroutes.list_instructor_exercises'))


@authroutes.route('/instructor/suggest-distractors', methods=['POST'])
@login_required_as_courseinstructor
def suggest_distractors():
    """API endpoint to suggest distractors for a question"""
    import json
    import syntacticmutator
    import ltlnode
    
    answer = request.form.get('answer', '')
    kind = request.form.get('kind', 'englishtoltl')
    
    distractors = []
    error = None
    
    if kind == 'englishtoltl':
        try:
            parsed = ltlnode.parse_ltl_string(answer)
            if parsed:
                mutations = syntacticmutator.getAllMutationsOf(parsed)
                for mutation in mutations:
                    distractors.append({
                        'formula': str(mutation['formula']),
                        'code': mutation['code']
                    })
        except Exception as e:
            error = str(e)
    
    return json.dumps({'distractors': distractors, 'error': error}), 200, {'Content-Type': 'application/json'}    
    return json.dumps({'distractors': distractors, 'error': error}), 200, {'Content-Type': 'application/json'}