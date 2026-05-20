import streamlit as st
from backened_with_tools import chatbot,retrive_old_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import uuid



st.header("Advance - Chatbot")

#  _______________________ UTILITY FUNCTIONS _________________________
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():  #imp
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []


def load_conversation(thread_id): # imp
    return chatbot.get_state(config={'configurable':{'thread_id': thread_id}}).values['messages']



# _____________________ SESSION SET UP _____________________________

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []   #[{'role': 'user'/'assistant', 'content': 'message content'}, {...}]



if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrive_old_threads()

add_thread(st.session_state['thread_id'])


# __________________  SIDEBAR ___________________

st.sidebar.title('Langgraph Chatbot')

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1] :
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg , HumanMessage):
                role = 'user'
            else :
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})  
        
        st.session_state['message_history'] = temp_messages  



# printing and loading convo history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


# take user input
user_input = st.chat_input("Type here ")

if user_input:

    st.session_state['message_history'].append({'role':'user','content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # CONFIG = {'configurable':{'thread_id':  st.session_state['thread_id']}}   
    CONFIG = {
            'configurable':{'thread_id':  st.session_state['thread_id']},
            'metadata': {'thread_id':  st.session_state['thread_id']},
            'run_name' : 'chat_turn' 
              }   

    with st.chat_message('assistant'):
        # small status container
        status_holder = {'box':None}
        
        
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": HumanMessage(content=user_input)},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk,ToolMessage):
                    tool_name = getattr(message_chunk,"name","tool")
                    if status_holder['box'] is None:
                        status_holder['box'] = st.status(f"⚙️ using `{tool_name}`...",expanded=True )
                    else:
                        status_holder["box"]. update(
                            label=f"' Using '{tool_name}' ... ",
                            state="running",
                            expanded=False)
                    

                # Detect if ai message 
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

                

                
        
        with st.status("Thinking...", expanded=True):
            ai_message = st.write_stream(ai_only_stream())

        if status_holder['box'] is not None:
            status_holder['box'].update(
                    label=f"✅ tool Finished",
                    state="complete",
                    expanded=False
                    )
        
    st.session_state['message_history'].append({'role':'assistant','content': ai_message }) 
