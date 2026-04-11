from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.checkpoint.memory import MemorySaver

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

# compile and preview 
checkpointer = MemorySaver()
chatbot = graph.compile(checkpointer=checkpointer)