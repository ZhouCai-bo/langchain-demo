import logging
import time

import streamlit as st
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from src.llm.chatbot import app


st.title("Talk To Me")

if 'messages' not in st.session_state:
    st.session_state.messages = []

def convert_messsages(messages: list[dict]):
    result = []
    for msg in messages:
        if msg['role'] == 'user':
            result.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            result.append(AIMessage(content=msg['content']))
    return result

def chat(messages: list[dict], language: str):
    print('messages')

    try:
        model_messages = convert_messsages(messages)
        config = {'Configurable': {'thread_id': '001'}}
        result = app.invoke(
            {'messages': model_messages, 'language': language},
            config,
        )
        print(result)
        return result['messages'][-1]

    except Exception as e:
        logging.error(f"Error during streaming: {str(e)}")
        raise e


def draw():
    st.sidebar.header("配置:")

    model = st.sidebar.selectbox("选择模型：", ["百度千帆"])
    language = st.sidebar.selectbox("选择语言：", ["汉语", "英语", "西班牙语", "德语", "法语"])

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
                        response_message = chat(messages, language)
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