from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer
from typing import List
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass
    
class ChatSession(Base):
    __tablename__ = "chat_session"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    cookie: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    messages: Mapped[List["Message"]] = relationship(back_populates="chat_session")
    
class Message(Base):
    __tablename__ = "message"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    origin: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # = mapped_column(String(10000))
    chat_session_id = mapped_column(ForeignKey("chat_session.id"))
    chat_session: Mapped["ChatSession"] = relationship(back_populates="messages")
    

