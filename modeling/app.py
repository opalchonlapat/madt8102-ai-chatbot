# these three lines swap the stdlib sqlite3 lib with the pysqlite3 package
# TODO: If trying this app locally, comment out these 3 lines
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# from dotenv import load_dotenv
from agent import *
from utils import *

import streamlit as st
import uuid
import os

# os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]

# load_dotenv(override=True)
str_content = "-" * 50
os_write(str_content)
str_content = f"LangSmith project name: {os.getenv('LANGCHAIN_PROJECT')}"
os_write(str_content)

# UI
st.set_page_config(
    page_title="HR Analytics",
    page_icon="🤖"
)

st.title("Employees Attendance Assistant")
avatar_assistant = "🤖"
# client = Client()

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    os.environ["OPENAI_API_KEY"] = openai_api_key
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    is_clear_msg = st.button("Clear message history")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
str_content = f"Thread ID: {st.session_state['thread_id']}"
os_write(str_content)

for msg in st.session_state["messages"]:
    if msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar=avatar_assistant).write(msg["content"])
    else:
        st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input(placeholder="Message for Assistant")
if user_input:
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    responses = run_agent(user_input=user_input, thread_id=st.session_state["thread_id"])
    # st.session_state["pre_defined_run_id"] = pre_defined_run_id
    last_response_message = responses['messages'][-1].content
    st.session_state["messages"].append({"role": "assistant", "content": last_response_message})
    st.chat_message("assistant", avatar=avatar_assistant).write(last_response_message)

if is_clear_msg:
    st.session_state.clear()
    st.rerun()