from flask import Flask, render_template, request, redirect, url_for, flash, current_app, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session, sessionmaker, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, create_engine, inspect, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from logger import get_db_uri

from flask import Blueprint, abort
import os
import random
import string
from functools import wraps
from urllib.parse import urlparse
from datetime import datetime, timezone
from ltlnode import SUPPORTED_SYNTAXES

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
    syntax = Column(String, nullable=True)  # Optional: fixed syntax for display
    exercise_json = Column(String)  # JSON string of the exercise questions
    created_at = Column(String)  # ISO timestamp
    updated_at = Column(String)  # ISO timestamp
    expires_at = Column(String, nullable=True)  # ISO timestamp when the exercise closes
    allow_multiple_submissions = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)  # Soft-delete flag to hide from students



class User(UserMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)
    # Optional credential. Populated for accounts that authenticate with a
    # password (instructors, and persistent student accounts); anonymous
    # students and quick course-code students leave it NULL.
    password_hash: Mapped[str] = mapped_column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class AnonymousStudent(User):
    __mapper_args__ = {
        'polymorphic_identity': 'anonymous-student',
    }


class CourseStudent(User):
    """A student account, identified by its (globally unique) username. The two
    fields below are optional and independent:

      * course_id     — set when the student is enrolled in a course (via a
                        course code at login/signup, or by joining one later).
      * password_hash — (inherited from User) set for a persistent account the
                        student can log back into from any device. A course-code
                        student with no password is quick to create but is bound
                        to the browser/device it was created in.

    So the same type covers a quick passwordless course-code student, a
    persistent password-protected student, and any combination (e.g. a
    persistent account that is also enrolled in a course)."""
    __mapper_args__ = {
        'polymorphic_identity': 'course-student',
    }

    course_id: Mapped[str] = mapped_column(String, nullable=True)


class CourseInstructor(User):
    __mapper_args__ = {
        'polymorphic_identity': 'course-instructor',
    }


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


def _ensure_instructor_exercise_schema():
    """Add newly introduced columns to the instructor exercises table if they are missing."""
    existing_columns = {col['name'] for col in inspector.get_columns(INSTRUCTOR_EXERCISE_TABLE)}

    with engine.begin() as connection:
        if 'expires_at' not in existing_columns:
            connection.execute(text(f"ALTER TABLE {INSTRUCTOR_EXERCISE_TABLE} ADD COLUMN expires_at VARCHAR"))

        if 'allow_multiple_submissions' not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE {INSTRUCTOR_EXERCISE_TABLE} "
                    "ADD COLUMN allow_multiple_submissions BOOLEAN DEFAULT TRUE"
                )
            )

        if 'is_deleted' not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE {INSTRUCTOR_EXERCISE_TABLE} "
                    "ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"
                )
            )
            connection.execute(
                text(
                    f"UPDATE {INSTRUCTOR_EXERCISE_TABLE} "
                    "SET is_deleted = FALSE WHERE is_deleted IS NULL"
                )
            )

        if 'syntax' not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE {INSTRUCTOR_EXERCISE_TABLE} "
                    "ADD COLUMN syntax VARCHAR"
                )
            )


_ensure_instructor_exercise_schema()

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


def _is_safe_next(next_page: str) -> bool:
    """Ensure the post-login redirect target stays on this site."""
    if not next_page:
        return False

    parsed = urlparse(next_page)

    # Disallow external hosts and schemes
    if parsed.netloc or parsed.scheme:
        return False

    # Only allow absolute paths within this application
    return parsed.path.startswith('/')


def _get_safe_next_param():
    """Return a sanitized `next` parameter or an empty string."""
    candidate = request.form.get('next') or request.args.get('next')
    return candidate if _is_safe_next(candidate) else ''


@authroutes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        next_page = _get_safe_next_param()
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

            elif user_type == 'student-account':
                ## Persistent student account: authenticate by password.
                username = request.form.get('username')
                password = request.form.get('password')
                user = session.query(CourseStudent).filter_by(username=username).first()

                canLogin = (user is not None) and user.check_password(password)

                if not canLogin:
                    flash('Invalid username or password.')
                    return redirect(url_for('authroutes.login'))

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
                return redirect(next_page or url_for('index'))
            else:
                flash('Login failed. Please try again.')
                return redirect(url_for('authroutes.login'))
    elif request.method == 'GET':
        # A course code no longer logs a student in on its own — it enrolls a
        # new, password-protected account. Old course links (?course_id=...)
        # therefore lead to sign-up, where the code is applied.
        course_id = request.args.get('course_id', '')
        if course_id:
            return redirect(url_for('authroutes.signup_student', course_id=course_id))
        next_page = _get_safe_next_param()
        return render_template('auth/login.html', next_page=next_page)
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


@authroutes.route('/signup-student', methods=['GET', 'POST'])
def signup_student():
    """Create a persistent, password-protected student account. Optionally
    enroll in a course at the same time by supplying a course code; the student
    can also join a course later from their home page."""
    if request.method == 'POST':
        with Session() as session:
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            course_code = (request.form.get('course_id') or '').strip()

            if not username or not password:
                flash('Username and password are required.')
                return render_template('auth/signup_student.html', course_id=course_code)

            if password != confirm_password:
                flash('Passwords do not match. Please try again.')
                return render_template('auth/signup_student.html', course_id=course_code)

            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                flash(f'Username {username} is already taken. Please choose another one.')
                return render_template('auth/signup_student.html', course_id=course_code)

            ## Optional enrollment: only accept a course code that exists.
            course_id = None
            if course_code:
                course = session.query(Course).filter_by(name=course_code).first()
                if course is None:
                    flash('Could not find a course with ID ' + course_code)
                    return render_template('auth/signup_student.html', course_id=course_code)
                course_id = course_code

            user = CourseStudent(username=username, course_id=course_id)
            user.set_password(password)
            session.add(user)
            session.commit()
            login_user(user)
            return redirect(url_for('index'))
    # GET: a course code may be supplied by a QR / shared link to pre-fill the form.
    return render_template('auth/signup_student.html', course_id=request.args.get('course_id', ''))


@authroutes.route('/join-course', methods=['POST'])
@login_required
def join_course():
    """Let a logged-in student enroll in a course by course code. Used by
    persistent students who signed up without a course."""
    if not isinstance(current_user, CourseStudent):
        abort(403)

    course_code = (request.form.get('course_id') or '').strip()
    with Session() as session:
        course = session.query(Course).filter_by(name=course_code).first()
        if course is None:
            flash('Could not find a course with ID ' + course_code)
            return redirect(url_for('index'))

        student = session.query(CourseStudent).filter_by(username=current_user.username).first()
        if student is not None:
            student.course_id = course_code
            session.commit()
            flash(f'You have joined the course {course_code}.')
    return redirect(url_for('index'))




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

            signup_link = url_for('authroutes.signup_student', course_id=course.name, _external=True)

            flash(f'Course <code>{coursename}</code> registered successfully. <br><br> Students join by creating an account at the sign-up link <code>{signup_link}</code> (the course code <code>{course.name}</code> is filled in for them) or with the course code directly. <br><br>This link, along with a scannable QR code, will also be available in your instructor dashboard.')
            return redirect(url_for('authroutes.register_exercise'))
    return render_template('instructorhome.html')


@authroutes.route('/course/<course_name>/qr.svg')
@login_required_as_courseinstructor
def course_login_qr(course_name):
    """Serve a QR code (SVG) encoding the student sign-up link for a course.
    Restricted to the instructor who owns the course. Students scan it to open
    the sign-up page with the course code pre-filled, and create a
    password-protected account enrolled in the course."""
    import io
    import segno

    with Session() as session:
        course = session.query(Course).filter_by(name=course_name).first()
        if course is None or course.owner != current_user.username:
            abort(404)

    signup_link = url_for(
        'authroutes.signup_student',
        course_id=course_name,
        _external=True,
    )
    qr = segno.make(signup_link, error='m')
    buf = io.BytesIO()
    qr.save(buf, kind='svg', scale=6, border=2)
    return Response(buf.getvalue(), mimetype='image/svg+xml')


def retrieve_course_data(course_name) -> Course:
    with Session() as session:
        exercise = session.query(Course).filter_by(name=course_name).first()
        return exercise

def get_owned_courses(username):
    with Session() as session:
        exercises = session.query(Course).filter_by(owner=username).all()
        return exercises


def get_course_students(course_name):
    """Return all students enrolled in a course."""
    with Session() as session:
        students = session.query(CourseStudent).filter_by(course_id=course_name).all()
        return students


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
        exercises = (
            session.query(InstructorExercise)
            .filter_by(owner=username, is_deleted=False)
            .all()
        )
        return exercises


def get_instructor_exercise_by_id(exercise_id):
    """Get a specific exercise by ID"""
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        return exercise


def get_exercises_for_course(course_name):
    """Get all exercises assigned to a specific course"""
    with Session() as session:
        exercises = (
            session.query(InstructorExercise)
            .filter_by(course=course_name, is_deleted=False)
            .all()
        )
        return exercises


def get_course_exercise_by_name(course_name, exercise_name):
    """Get a single exercise for a course by its display name."""
    with Session() as session:
        return (
            session.query(InstructorExercise)
            .filter_by(course=course_name, name=exercise_name, is_deleted=False)
            .first()
        )


def get_instructor_exercise_by_name(exercise_name):
    """Get the first exercise matching a given name (regardless of course)."""
    with Session() as session:
        return (
            session.query(InstructorExercise)
            .filter_by(name=exercise_name, is_deleted=False)
            .first()
        )


def normalize_syntax_choice(raw_syntax):
    syntax = (raw_syntax or '').strip()
    return syntax if syntax in SUPPORTED_SYNTAXES else None


def parse_expires_at(expires_at_str):
    if not expires_at_str:
        return None
    try:
        return datetime.fromisoformat(expires_at_str)
    except ValueError:
        return None


def is_exercise_expired(exercise, now=None):
    """Return True if the exercise has an expiry and it is in the past."""
    expires_at = parse_expires_at(exercise.expires_at)
    if not expires_at:
        return False

    now = now or datetime.utcnow()
    # Treat naive datetimes as UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now > expires_at


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
        syntax_choice = normalize_syntax_choice(request.form.get('exercise_syntax', ''))
        expires_at_raw = request.form.get('expires_at', '').strip()
        allow_multiple_submissions = request.form.get('submission_limit', 'multiple') == 'multiple'
        
        if not exercise_name:
            flash('Exercise name is required.')
            return redirect(url_for('authroutes.create_instructor_exercise'))
        
        # Validate JSON
        try:
            questions = json.loads(exercise_json)
            if not isinstance(questions, list):
                raise ValueError("Exercise must be a list of questions")
            exercise_json = json.dumps(questions)
            question_count = len(questions)
        except (json.JSONDecodeError, ValueError) as e:
            flash(f'Invalid exercise JSON: {str(e)}')
            return redirect(url_for('authroutes.create_instructor_exercise'))

        expires_at_value = None
        if expires_at_raw:
            try:
                expires_at_dt = datetime.fromisoformat(expires_at_raw)
                expires_at_value = expires_at_dt.isoformat()
            except ValueError:
                flash('Invalid expiry date/time.')
                return redirect(url_for('authroutes.create_instructor_exercise'))
        
        now = datetime.utcnow().isoformat()
        
        with Session() as session:
            exercise = InstructorExercise(
                name=exercise_name,
                owner=current_user.username,
                course=course if course else None,
                syntax=syntax_choice,
                exercise_json=exercise_json,
                created_at=now,
                updated_at=now,
                expires_at=expires_at_value,
                allow_multiple_submissions=allow_multiple_submissions
            )
            session.add(exercise)
            session.commit()
            exercise_id = exercise.id
        
        flash(f'Exercise "{exercise_name}" created successfully with {question_count} question(s).')
        return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
    
    # GET request - show the exercise builder
    owned_courses = get_owned_courses(current_user.username)
    course_names = [c.name for c in owned_courses]
    return render_template('instructor/exercise_builder.html', 
                           exercise=None,
                           course_names=course_names,
                           supported_syntaxes=SUPPORTED_SYNTAXES)


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
            syntax_choice = normalize_syntax_choice(request.form.get('exercise_syntax', ''))
            expires_at_raw = request.form.get('expires_at', '').strip()
            allow_multiple_submissions = request.form.get('submission_limit', 'multiple') == 'multiple'
            
            if not exercise_name:
                flash('Exercise name is required.')
                return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
            
            # Validate JSON
            try:
                questions = json.loads(exercise_json)
                if not isinstance(questions, list):
                    raise ValueError("Exercise must be a list of questions")
                exercise_json = json.dumps(questions)
                question_count = len(questions)
            except (json.JSONDecodeError, ValueError) as e:
                flash(f'Invalid exercise JSON: {str(e)}')
                return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))

            expires_at_value = None
            if expires_at_raw:
                try:
                    expires_at_dt = datetime.fromisoformat(expires_at_raw)
                    expires_at_value = expires_at_dt.isoformat()
                except ValueError:
                    flash('Invalid expiry date/time.')
                    return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
            
            exercise.name = exercise_name
            exercise.exercise_json = exercise_json
            exercise.course = course if course else None
            exercise.syntax = syntax_choice
            exercise.updated_at = datetime.utcnow().isoformat()
            exercise.expires_at = expires_at_value
            exercise.allow_multiple_submissions = allow_multiple_submissions
            session.commit()
            
            flash(f'Exercise "{exercise_name}" updated successfully with {question_count} question(s).')
            return redirect(url_for('authroutes.edit_instructor_exercise', exercise_id=exercise_id))
        
        # GET request
        owned_courses = get_owned_courses(current_user.username)
        course_names = [c.name for c in owned_courses]
        
        # Make a copy of the exercise data to pass to the template
        exercise_data = {
            'id': exercise.id,
            'name': exercise.name,
            'course': exercise.course,
            'syntax': exercise.syntax,
            'exercise_json': exercise.exercise_json,
            'created_at': exercise.created_at,
            'updated_at': exercise.updated_at,
            'expires_at': exercise.expires_at,
            'allow_multiple_submissions': exercise.allow_multiple_submissions
        }
        
    return render_template('instructor/exercise_builder.html', 
                           exercise=exercise_data,
                           course_names=course_names,
                           supported_syntaxes=SUPPORTED_SYNTAXES)


@authroutes.route('/instructor/exercises/<int:exercise_id>/delete', methods=['POST'])
@login_required_as_courseinstructor
def delete_instructor_exercise(exercise_id):
    """Soft-delete an exercise so it is hidden from students."""
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()

        if not exercise:
            flash('Exercise not found.')
            return redirect(url_for('authroutes.list_instructor_exercises'))
        
        if exercise.owner != current_user.username:
            flash('You do not have permission to delete this exercise.')
            return redirect(url_for('authroutes.list_instructor_exercises'))

        exercise_name = exercise.name
        exercise.is_deleted = True
        exercise.updated_at = datetime.utcnow().isoformat()
        session.commit()

        flash(f'Exercise "{exercise_name}" deleted for students.')
    
    return redirect(url_for('authroutes.list_instructor_exercises'))


@authroutes.route('/instructor/suggest-distractors', methods=['POST'])
@login_required_as_courseinstructor
def suggest_distractors():
    """API endpoint to suggest distractors for a question"""
    from flask import jsonify
    import ltlnode
    from codebook import getAllApplicableMisconceptions
    
    answer = request.form.get('answer', '')
    kind = request.form.get('kind', 'englishtoltl')
    
    distractors = []
    error = None
    
    if kind == 'englishtoltl':
        try:
            parsed = ltlnode.parse_ltl_string(answer)
            if parsed:
                # Use the same approach as authorquestion in app.py
                applicable = getAllApplicableMisconceptions(parsed)
                for misconception in applicable:
                    distractors.append({
                        'formula': str(misconception.node),
                        'code': str(misconception.misconception)
                    })
                
                # Merge labels for equal formulae
                merged = []
                for distractor in distractors:
                    existing = next((d for d in merged if d['formula'] == distractor['formula']), None)
                    if existing:
                        existing['code'] += f", {distractor['code']}"
                    else:
                        merged.append(distractor)
                distractors = merged
        except Exception as e:
            error = str(e)
    
    return jsonify({'distractors': distractors, 'error': error})


@authroutes.route('/instructor/suggest-traces', methods=['POST'])
@login_required_as_courseinstructor
def suggest_traces():
    """API endpoint to suggest traces for trace satisfaction questions"""
    from flask import jsonify
    import spotutils
    import exerciseprocessor
    import ltlnode
    
    formula = request.form.get('formula', '')
    
    satisfying_traces = []
    rejecting_traces = []
    error = None
    
    try:
        # Parse and validate the formula
        parsed = ltlnode.parse_ltl_string(formula)
        formula_str = str(parsed)
        
        # Get literals from formula for trace expansion
        literals = list(exerciseprocessor.getFormulaLiterals(formula_str))
        
        # Generate satisfying traces
        sat_traces = spotutils.generate_accepted_traces(formula_str, max_traces=5)
        for trace in sat_traces:
            trace_str = exerciseprocessor.canonicalizeSpotTrace(str(trace))
            expanded = exerciseprocessor.expandSpotTrace(trace_str, literals)
            trace_data = exerciseprocessor.traceToRenderData(expanded)
            satisfying_traces.append({
                'trace': expanded,
                'raw': trace_str,
                'trace_data': trace_data,
                'satisfies': True
            })
        
        # Generate rejecting traces (traces that satisfy NOT formula)
        negated = f"!({formula_str})"
        rej_traces = spotutils.generate_accepted_traces(negated, max_traces=5)
        for trace in rej_traces:
            trace_str = exerciseprocessor.canonicalizeSpotTrace(str(trace))
            expanded = exerciseprocessor.expandSpotTrace(trace_str, literals)
            trace_data = exerciseprocessor.traceToRenderData(expanded)
            rejecting_traces.append({
                'trace': expanded,
                'raw': trace_str,
                'trace_data': trace_data,
                'satisfies': False
            })
            
    except Exception as e:
        error = str(e)
    
    return jsonify({
        'satisfying': satisfying_traces,
        'rejecting': rejecting_traces,
        'error': error
    })
