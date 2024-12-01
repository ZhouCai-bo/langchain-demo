import logging
import time
from typing import Sequence
from typing_extensions import Annotated, TypedDict

import streamlit as st
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import QianfanChatEndpoint
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, add_messages
# from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, trim_messages


ak = 'MSh0vo1NQTErNMBGlcnODVvi'
sk = '3Yhn7t0JZmUj6Zf2S0g4veuPARevlCOv'


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
    summary: str

model = QianfanChatEndpoint(tampreture=0.1, timeout=10, api_key=ak, secret_key=sk) 
prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            '你是一位专家助手，请使用{language}，尽可能的回答问题。'
        ),
        MessagesPlaceholder(variable_name='messages'),
    ]
)

workflow = StateGraph(state_schema=State)

trimmer = trim_messages(
    max_tokens=150,
    strategy='last',
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on='human',
)

def call_model(state: State, messages: list[BaseMessage]=None):
    print('State before call')
    print(len(state['messages']) ,' messgaes in state')
    chain = prompt | model
    if not messages:
        trimmed_messages = trimmer.invoke(state['messages'])
        print(111)
    else:
        trimmed_messages = trimmer.invoke(messages)
        print(222)
    print('trimmed message')
    print(trimmed_messages)
    response = chain.invoke({
        'messages': trimmed_messages,
        'language': state['language']
    })
    print('State after call')
    print(len(state['messages']) ,' messgaes in state')
    return {'messages': [response]}


workflow.add_edge(START, 'model')
workflow.add_node('model', call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


def trim_messages(messages: list[BaseMessage]):
    return trimmer.invoke(messages)

def summary_messages(state: State):
    summary = state.get('summary', '')
    if summary:
        summary_message = f'这是一段对话的总结：{summary}\n\n，使用下面的消息扩充这一份总结:'
    else:
        summary_message = '总结下面的对话:'

    messages = state['message'] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    delete_messages

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
        config = {'configurable': {'thread_id': '001'}}
        result = app.invoke(
            {'messages': model_messages, 'language': language},
            config,
        )
        print(result)
        return result['messages'][-1].content

    except Exception as e:
        logging.error(f"Error during streaming: {str(e)}")
        raise e


def draw():
    st.title("Talk To Me")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

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