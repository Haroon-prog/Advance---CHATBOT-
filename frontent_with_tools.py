import streamlit as st
from backened_with_tools import chatbot,retrive_old_threads
from langchain_core.messages import HumanMessage,AIMessage
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
        status_box = st.status("Thinking...", expanded=False)

        tool_used = False

        def ai_only_stream():
            global tool_used

            for message_chunk, metadata in chatbot.stream(
                {"messages": HumanMessage(content=user_input)},
                config=CONFIG,
                stream_mode="messages"
            ):

                # Detect tool calls
                if isinstance(message_chunk, AIMessage):

                    # if tools are called
                    if hasattr(message_chunk, "tool_calls") and message_chunk.tool_calls:
                        tool_used = True

                        tool_names = [
                            tool["name"] for tool in message_chunk.tool_calls
                        ]

                        status_box.update(
                            label=f"Using Tool: {', '.join(tool_names)}",
                            state="running"
                        )

                    # stream assistant text only
                    if message_chunk.content:
                        yield message_chunk.content

            # final status update
            if tool_used:
                status_box.update(
                    label="Response generated using tools",
                    state="complete"
                )
            else:
                status_box.update(
                    label="Response generated without tools",
                    state="complete"
                )

        ai_message = st.write_stream(ai_only_stream())
        
    st.session_state['message_history'].append({'role':'assistant','content': ai_message }) 
