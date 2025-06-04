from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker#, Session

DATABASE_URL = "sqlite:///messages.db"  # Change to your preferred database
engine = create_engine(DATABASE_URL, echo=True)

def create_database():
    Base.metadata.create_all(engine)
    
def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
    #return Session(engine)
