
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.graph.message import add_messages  #add messages convo to msgs in state
import sqlite3
import requests

load_dotenv()
llm = ChatGroq(model="llama-3.1-8b-instant")

# ------------------------
# tools 
# ------------------------

search_tool = DuckDuckGoSearchRun()

@tool
def calculator(first_num : float , second_num:float, operation: str) -> dict:
    """ Perform a basic arithmetic operation on 2 numbers
    Supported operations : add, sub, mul, div """

    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return{'error' : f"Unsupported operation '{operation}'"}
        
        return {"first_num" : first_num, "second_num" : second_num, "operation": operation, "result": result}
    except Exception as e :
        return {'error': str(e)}
    

@tool
def get_stock_price(symbol : str) -> dict:
    """ 
    fetch latest stock price for a given symbol (eg: 'AAPL', 'TSLA')
    Using alpha vantage API key in URL
    """

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey= 5JQYORLNFTXV0WNU"
    r = requests.get(url)

    return r.json()


tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)




# ----------------------
# state
# ----------------------
class chatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]



# ----------------------
# Nodes 
# ----------------------
def chat_node(state : chatState) -> chatState:
    """ LLM node that may answer to general messages or may request a tool call if necessary"""
    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


tool_node = ToolNode(tools)    #execute tool calls 



# ----------------------
# checkpointer
# ----------------------

# database integration 
conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
# checkpointer
checkpointer = SqliteSaver(conn=conn)



# ----------------------
# Graph 
# ----------------------
graph = StateGraph(chatState)
# add node 
graph.add_node('chat_node',chat_node)
graph.add_node('tools' ,tool_node)

# add edge 
graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge("tools", "chat_node")

# # compile and preview 
chatbot = graph.compile(checkpointer=checkpointer)



# ----------------------
# Helper function 
# ----------------------
def retrive_old_threads():
    all_threads = set()   #as set only stores unique values , so it will not store repeated value 
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads) 