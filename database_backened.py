from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()


from langgraph.graph.message import add_messages
class chatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]


llm = ChatGroq(model="llama-3.1-8b-instant")
def chat_node(state : chatState) -> chatState:
    messages = state["messages"]

    response = llm.invoke(messages)

    return {"messages": response}



graph = StateGraph(chatState)
# add node 
graph.add_node('chat_node',chat_node)

# add edge 
graph.add_edge(START,'chat_node')
graph.add_edge('chat_node',END)

# database integration 
conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
# checkpointer
checkpointer = SqliteSaver(conn=conn)



# # compile and preview 
chatbot = graph.compile(checkpointer=checkpointer)


def retrive_old_threads():
    all_threads = set()   #as set only stores unique values , so it will not store repeated value 
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads) 