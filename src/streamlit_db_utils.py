from models import ChatSession, Message
from database import get_session
import uuid
import streamlit as st
import json
from langchain.schema import HumanMessage as HMessage, AIMessage


s = get_session()

def get_messages(cookie_id):
    chat_session = s.query(ChatSession).filter_by(cookie=cookie_id).first()
    if not chat_session:
        return [], []
 
    messages_list = [
        {"role": "user" if msg.origin == 1 else "assistant", "content": msg.text}
        for msg in chat_session.messages
    ]
    new_messages_model = [
        HMessage(content=msg.text) if msg.origin == 1 else AIMessage(content=msg.text)
        for msg in chat_session.messages
    ]
    return messages_list, new_messages_model

def setup_db(controller):
    if controller.get("id"):
        st.session_state["id"] = controller.get("id")
        st.session_state["messages"], new_messages_model = get_messages(st.session_state["id"])
        if new_messages_model != []:
            config = {"configurable": {"thread_id": "1"}}
            st.session_state["app"].update_state(config, {"messages": new_messages_model})
    else:
        st.session_state["id"] = str(uuid.uuid4())
        controller.set("id", st.session_state["id"])

        st.session_state["messages"] = []

def get_or_create_chat_session(s, cookie):
    cs = s.query(ChatSession).filter_by(cookie=cookie).first()
    if not cs:
        cs = ChatSession(cookie=cookie)
        s.add(cs)
        s.commit()
    return cs

def add_message(cookie_id, message:str, origin: int):
    cs = get_or_create_chat_session(s, cookie_id)
    #print(cs.id)
    m = Message(text=message, origin=origin, chat_session=cs)
    s.add(m)
    s.commit()





"""
s = get_session()
cookie = str(uuid.uuid4())
cs = ChatSession(cookie=cookie)

s.add(cs)
s.commit()

add_message(s, cookie, "Primer absurdo mensaje", origin=0)
add_message(s, cookie, "Segundo absurdo mensaje", origin=1)

for m in cs.messages:
    print(m.id, m.text)
"""