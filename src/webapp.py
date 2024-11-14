import logging
import time

import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.chat_models import QianfanChatEndpoint
from langchain_core.messages.ai import AIMessage, AIMessageChunk
from langchain_core.messages.human import HumanMessage, HumanMessageChunk


st.title("Chat with LLMs Models")  # Set the title of the Streamlit app

if 'messages' not in st.session_state:
    st.session_state.messages = []

def stream_chat(model, messages, ak, sk):
    ak = 'MSh0vo1NQTErNMBGlcnODVvi'
    sk = '3Yhn7t0JZmUj6Zf2S0g4veuPARevlCOv'
    print('messages')
    # for msg in messages:
    #     print(msg)
    # try:
    #     llm = QianfanChatEndpoint(tampreture=0.1, timeout=10, api_key=ak, secret_key=sk) 
    #     memory = ConversationBufferMemory()
    #     original_chain = ConversationChain(
    #         llm=llm,
    #         verbose=True,
    #         memory=memory,
    #     )
    #     resp = original_chain.run(messages[-1]['content'])
    #     print(memory.load_memory_variables({}))
    #     return resp
    # except Exception as e:
    #     # Log and re-raise any errors that occur
    #     logging.error(f"Error during streaming: {str(e)}")
    #     raise e

    # sequence = []
    # for msg in messages:
    #     if msg["role"] == "user":
    #         sequence.append(HumanMessage(msg['content']))
    #     else:
    #         sequence.append(AIMessage(msg['content']))

    try:
        llm = QianfanChatEndpoint(tampreture=0.1, timeout=10, api_key=ak, secret_key=sk) 
        memory = ConversationBufferMemory()
        for i in range(0, len(messages) - 2, 2):
            memory.save_context({'Human': messages[i]['content']}, {'AI': messages[i+1]['content']})

        original_chain = ConversationChain(
            llm=llm,
            verbose=True,
            memory=memory,
        )
        resp = original_chain.run(messages[-1]['content'])
        print(memory.load_memory_variables({}))
        return resp
    except Exception as e:
        # Log and re-raise any errors that occur
        logging.error(f"Error during streaming: {str(e)}")
        raise e


def draw():
    #defining side bar
    st.sidebar.header("Filters:")

    ak = st.sidebar.text_input(label='千帆AK：')
    sk = st.sidebar.text_input(label='千帆SK：', type="password")

    # Sidebar for model selection
    model = st.sidebar.selectbox("Choose a model", ["百度千帆"])

    # Prompt for user input and save to chat history
    if prompt := st.chat_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display the user's query
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["role"] == "assistant":
                    st.write("\n\nDuration: %s" % message["duration"])

        # Generate a new response if the last message is not from the assistant
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                start_time = time.time()  # Start timing the response generation

                with st.spinner("Writing..."):
                    try:
                        # Prepare messages for the LLM and stream the response
                        # messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in st.session_state.messages]
                        messages = st.session_state.messages
                        response_message = stream_chat(model, messages, ak, sk)
                        duration = time.time() - start_time  # Calculate the duration
                        # response_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                        st.session_state.messages.append({"role": "assistant", "content": response_message, 'duration': f'{duration:.2f} seconds'})
                        st.write(f"{response_message}\n\nDuration: {duration:.2f} seconds")
                        # st.write(f"Duration: {duration:.2f} seconds")
                        logging.info(f"Response: {response_message}, Duration: {duration:.2f} s")

                    except Exception as e:
                        # Handle errors and display an error message
                        st.session_state.messages.append({"role": "assistant", "content": str(e)})
                        st.error("An error occurred while generating the response.")
                        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    draw()