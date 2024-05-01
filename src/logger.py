##  {'date': '2023-01-01', 'concept': 'Concept A', 'frequency': 5}, ##

### TODO: Very much work in progress
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

### TODO ###
## This should wrap python logging module
## and eventually log somewhere.

### OR ###
## This should batch logs to a database
## Maybe use SQLAlchemy for this.

Base = declarative_base()

### This needs to be significantly extended ###
class Log(Base):
    __tablename__ = 'answer_logs'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    date = Column(DateTime)
    concept = Column(String)

class Logger:
    def __init__(self):
        self.engine = create_engine('sqlite:///logs.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def record(self, log_entry):
        self.session.add(log_entry)
        self.session.commit()
    
    ## We should log all responses here (NL Question, Correct Answer, Options, Selected, misconceptions, timestamp, isCorrect
    def logMisconceptions(self, studentId, misconceptions):
        for misconception in misconceptions:
            log = Log(student_id=studentId, date=datetime.datetime.now(), code=misconception)
            self.record(log)
    
    def getStudentLogs(self, studentId, lookback_days=30):
        lookback_date = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
        logs = self.session.query(Log).filter(Log.student_id == studentId, Log.date >= lookback_date).all()
        return logs

