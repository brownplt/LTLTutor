

### TODO: Very much work in progress
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy import inspect
from sqlalchemy.orm import scoped_session, sessionmaker


STUDENT_RESPONSE_TABLE = 'student_responses'

Base = declarative_base()

### This needs to be significantly extended ###
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


class Logger:
    def __init__(self):

        
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Create a path to the database file
        db_path = os.path.join(script_dir, 'database.db')

        # Create the engine
        self.engine = create_engine(f'sqlite:///{db_path}')

        #self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        self.inspector = inspect(self.engine)
        if STUDENT_RESPONSE_TABLE not in self.inspector.get_table_names():
            Base.metadata.tables[STUDENT_RESPONSE_TABLE].create(self.engine)


    
    def record(self, log):
        session = self.Session()
        session.add(log)
        session.commit()
    
    def logStudentResponse(self, userId, misconceptions, question_text, question_options, correct_answer, questiontype):

        ## HACK: Shouldn't have to do this here  again ##
        if STUDENT_RESPONSE_TABLE not in self.inspector.get_table_names():
            Base.metadata.tables[STUDENT_RESPONSE_TABLE].create(self.engine)

        for misconception in misconceptions:

            ## Ensure everything is of the correct type
            if not isinstance(userId, str):
                raise ValueError("userId should be an integer")
            if not isinstance(misconception, str):
                raise ValueError("misconception should be a string")
            if not isinstance(question_text, str):
                raise ValueError("question_text should be a string")
            if not isinstance(question_options, str):
                raise ValueError("question_options should be a string")
            if not isinstance(correct_answer, bool):
                raise ValueError("correct_answer should be a boolean")
            if not isinstance(questiontype, str):
                raise ValueError("questiontype should be a string")

            log = StudentResponse(user_id=userId, timestamp=datetime.datetime.now(), 
                                  misconception=misconception, question_text=question_text, question_options=question_options, correct_answer=correct_answer,
                                  question_type=questiontype)
            self.record(log)
    
    def getUserLogs(self, userId, lookback_days=30):
        if not isinstance(userId, str):
            raise ValueError("userId should be an integer")

        session = self.Session()

        lookback_date = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
        logs = session.query(StudentResponse).filter(StudentResponse.user_id == userId, StudentResponse.timestamp >= lookback_date).all()
        return logs

