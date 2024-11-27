# from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from utils import *

import streamlit as st
import warnings
import os
import uuid

warnings.filterwarnings('ignore')
# load_dotenv(override=True)
    
class Agent:

    def __init__(self, model, tools, memory, system_prompt=""):
        self.model = model.bind_tools(tools)
        self.tools = tools
        self.memory = memory
        self.system_prompt = system_prompt
        graph = StateGraph(MessagesState)
        graph.add_node("llm", self.call_llm)
        graph.add_node("tools", ToolNode(self.tools))
        # graph.add_edge(START, "assistant")
        graph.add_conditional_edges(
            "llm",
            # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
            # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
            tools_condition,
        )
        graph.add_edge("tools", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=self.memory)

    def call_llm(self, state: MessagesState):
        messages = state['messages']
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

# Streamlit runs your script from top to bottom at every user interaction or code change.
@st.cache_resource
def init_object():
    ### initialize ###
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0
    )
    str_content = f"Initialized LLM and Embedding model..."
    os_write(str_content)

    ### vector db ###
    current_directory = os.path.dirname(os.path.abspath(__file__))
    vector_store_path = os.path.join(current_directory, 'vector_store')
    vector_store = Chroma(
        collection_name="attendance_policy_v3",
        embedding_function=embeddings,
        persist_directory=vector_store_path
    )
    str_content = f"Number of vectors in vector DB: {vector_store._collection.count()}"
    os_write(str_content)

    # SQLite connects to file-based databases
    db_path = os.path.join(current_directory, 'employee.db')
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    str_content = f"Table name in SQL DB: {db.get_usable_table_names()}"
    os_write(str_content)

    ### retrieval ###
    policy_retrieval = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    ### tools ###
    @tool
    def get_attendance_policy(query: str) -> str:
        """Use this tool to retrieve company attendance policies."""
        similar_docs = policy_retrieval.invoke(query)  
        doc_content = ""
        for doc in similar_docs:
            doc_content += doc.page_content
            doc_content += "\n\n"
        return doc_content
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools.append(get_attendance_policy)
    for i, t in enumerate(tools):
        str_content = f"Tool {i}: {t.name}"
        os_write(str_content)

    ### system prompt ###
    system_prompt = """
    You are an agent designed to assist with HR analytics using two toolkits: attendance policy retrieval and employee single view SQL database. Follow the instructions below to effectively utilize these toolkits.

    - **Attendance Policy Questions**: Use the `get_attendance_policy` tool to retrieve relevant policies.

    - **Employee Single View SQL Database Questions**:
    - Use the following sequence of SQL toolkits:
        1. `sql_db_list_tables`
        2. `sql_db_schema`
        3. `sql_db_query_checker`
        4. `sql_db_query`
    - Create a syntactically correct SQLite query to address the user's question.
    - Limit the query to at most 5 results unless the user specifies otherwise.
    - Order the results by a relevant column to provide the most interesting examples.
    - Only query for relevant columns, not all columns from a table.
    - Double-check your query for correctness before execution.
    - If an error occurs during execution, rewrite and retry the query.
    - Do not perform any DML operations (INSERT, UPDATE, DELETE, DROP, etc.).

    - **Non-Toolkit Related Questions**: Inform the user that you can only assist with attendance policy and employee-related questions.

    # Steps

    1. Determine if the question is related to attendance policy or employee data.
    2. For attendance policy questions, use the `get_attendance_policy` tool.
    3. For employee data questions, follow the SQL toolkit sequence to construct and execute a query.
    4. If the question is unrelated to the toolkits, inform the user of your limitations.

    # Output Format

    - Provide a clear and concise answer based on the retrieved data or policy.
    - For SQL queries, present the results in a tabular format or as a list, highlighting key information.

    # Examples

    **Example 1: Attendance Policy Question**
    - **Input**: "What is the policy for remote work attendance?"
    - **Output**: Use `get_attendance_policy` to retrieve and present the relevant policy details.

    **Example 2: Employee Data Question**
    - **Input**: "Show me the top 5 employees with the highest attendance this month."
    - **Output**: 
    - Use SQL toolkits to construct a query.
    - Present the top 5 employees with their attendance records.

    # Notes

    - Always ensure the query is syntactically correct and relevant to the question.
    - Handle errors gracefully by rewriting and retrying queries if necessary.
    - Clearly communicate any limitations in your capabilities to the user.
    """.strip()

    ### agent ###
    ai_agent = Agent(
        model=llm,
        tools=tools,
        memory=MemorySaver(),
        system_prompt=system_prompt
    )
    return ai_agent.graph

def run_agent(user_input: str, thread_id: str):
    react_graph_memory = init_object()

    # Specify a thread
    config = {"configurable": {"thread_id": thread_id}}

    # run
    messages = [HumanMessage(content=user_input)]
    messages = react_graph_memory.invoke({"messages": messages}, config)
    return messages