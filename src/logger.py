import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy import inspect
from sqlalchemy.orm import scoped_session, sessionmaker


STUDENT_RESPONSE_TABLE = 'student_responses'
GENERATED_EXERCISE_TABLE = 'generated_exercise'



def get_db_uri():
    ### If running in heroku, I want to use the postgres database
    if 'DATABASE_URL' in os.environ:
        db_uri = os.environ['DATABASE_URL']
        if db_uri.startswith("postgres://"):
            db_uri = db_uri.replace("postgres://", "postgresql://", 1)
        print(f"Using HEROKU PROVIDED database at {db_uri}, which was generated by replacing uri at {os.environ['DATABASE_URL']}")
        return db_uri
    else:   
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Create a path to the database file
        db_dir = os.path.join(script_dir, 'db')

        # Create directory db_dir if it doesn't exist
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)


        db_path = os.path.join(db_dir, 'database.db')
        print("Using file-based database at ", db_path)
        return f'sqlite:///{db_path}'

Base = declarative_base()


class StudentResponse(Base):
    __tablename__ = STUDENT_RESPONSE_TABLE
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    timestamp = Column(DateTime)
    misconception = Column(String)
    question_text = Column(String)
    question_options = Column(String)
    correct_answer = Column(Boolean)
    question_type = Column(String)
    mp_class = Column(String)
    exercise = Column(String)
    course = Column(String, default="")


class GeneratedExercise(Base):
    __tablename__ = GENERATED_EXERCISE_TABLE
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    timestamp = Column(DateTime)
    exercise_data = Column(String)
    complexity = Column(Integer)
    exerciseName = Column(String)

class Logger:
    def __init__(self):

        db_uri = get_db_uri()
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=True)
        self.Session = scoped_session(self.session_factory)

        self.inspector = inspect(self.engine)
        if STUDENT_RESPONSE_TABLE not in self.inspector.get_table_names():
            Base.metadata.tables[STUDENT_RESPONSE_TABLE].create(self.engine)

        if GENERATED_EXERCISE_TABLE not in self.inspector.get_table_names():
            Base.metadata.tables[GENERATED_EXERCISE_TABLE].create(self.engine)

    def record(self, log):
        with self.Session() as session:
            session.add(log)
            session.commit()

    
    def logStudentResponse(self, userId, misconceptions, question_text, question_options, correct_answer, questiontype, mp_class, exercise, course):

        if not isinstance(userId, str):
            raise ValueError("userId should be a string")
        if not isinstance(question_text, str):
            raise ValueError("question_text should be a string")
        if not isinstance(question_options, str):
            raise ValueError("question_options should be a string")
        if not isinstance(correct_answer, bool):
            raise ValueError("correct_answer should be a boolean")
        if not isinstance(questiontype, str):
            raise ValueError("questiontype should be a string")
        if not isinstance(mp_class, str):
            raise ValueError("mp_class should be a string")
        if not isinstance(exercise, str):
            raise ValueError("exercise should be a string")
        
        if not isinstance(course, str):
            raise ValueError("course should be a string")

        ## We still want to log the response if there are no misconceptions
        if misconceptions == None or len(misconceptions) == 0:
            log = StudentResponse(user_id=userId, timestamp=datetime.datetime.now(), 
                                  misconception="", question_text=question_text, question_options=question_options, correct_answer=correct_answer,
                                  question_type=questiontype, mp_class=mp_class, exercise=exercise, course=course)
            self.record(log)



        for misconception in misconceptions:
            if not isinstance(misconception, str):
                raise ValueError("misconception should be a string")

            log = StudentResponse(user_id=userId, timestamp=datetime.datetime.now(), 
                                  misconception=misconception, question_text=question_text, question_options=question_options, correct_answer=correct_answer,
                                  question_type=questiontype, mp_class=mp_class, exercise=exercise, course=course)
            self.record(log)

    
    def getUserLogs(self, userId, lookback_days=30):
        if not isinstance(userId, str):
            raise ValueError("userId should be a string")

        with self.Session() as session:
            lookback_date = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
            logs = session.query(StudentResponse).filter(StudentResponse.user_id == userId, StudentResponse.timestamp >= lookback_date).all()
            return logs


    def recordGeneratedExercise(self, userId, exercise_data, exercise_name):
        if not isinstance(userId, str):
            raise ValueError("userId should be a string")
        if not isinstance(exercise_data, str):
            raise ValueError("exercise_data should be a string")
        
        log = GeneratedExercise(user_id=userId, timestamp=datetime.datetime.now(), exercise_data=exercise_data, exerciseName=exercise_name)
        self.record(log)

    def getComplexity(self, userId):
        if not isinstance(userId, str):
            raise ValueError("userId should be a string")

        with self.Session() as session:
            complexity = session.query(GeneratedExercise.complexity).filter(GeneratedExercise.user_id == userId).order_by(GeneratedExercise.timestamp.desc()).first()
            return complexity[0] if complexity else None
    

    def getUserExercises(self, userId, lookback_days=30):
        if not isinstance(userId, str):
            raise ValueError("userId should be a string")

        with self.Session() as session:
            lookback_date = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
            logs = session.query(GeneratedExercise).filter(GeneratedExercise.user_id == userId, GeneratedExercise.timestamp >= lookback_date).all()
            return logs
        
    def getCourseResponses(self, course_name):
        if not isinstance(course_name, str):
            raise ValueError("exercise_name should be a string")

        with self.Session() as session:
            student_responses = session.query(StudentResponse).filter(StudentResponse.course == course_name).all()
            return student_responses
    