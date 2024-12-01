import logging
import time
from typing import Sequence, Literal
from typing_extensions import Annotated, TypedDict

import streamlit as st
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, RemoveMessage
from langchain.chat_models import QianfanChatEndpoint
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, add_messages, END
# from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


ak = 'MSh0vo1NQTErNMBGlcnODVvi'
sk = '3Yhn7t0JZmUj6Zf2S0g4veuPARevlCOv'


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
    summary: str


model = QianfanChatEndpoint(tampreture=0.1, timeout=10, api_key=ak, secret_key=sk) 

def call_model(state: State):
    summary = state.get("summary", "")
    if summary:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    'system',
                    '你是一位情感专家，善于帮助人们解决生活中遇到的情感问题，请使用{language}开展对话。\n注意要站在对方的角度，不要回答一些空话和大话，尝试提供一些安慰。先前的对话是:{summary}'
                ),
                MessagesPlaceholder(variable_name='messages'),
            ]
        )
    else:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    'system',
                    '你是一位情感专家，善于帮助人们解决生活中遇到的情感问题，请使用{language}开展对话。\n注意要站在对方的角度，不要回答一些空话和大话，尝试提供一些安慰。'
                ),
                MessagesPlaceholder(variable_name='messages'),
            ]
        )

    prompt_as_string = prompt.format(
        messages=state['messages'],
        language=state['language'],
        summary=state.get('summary', ''),
    )
    print('prompt')
    print(prompt_as_string)

    chain = prompt | model
    response = chain.invoke({
        'messages': state['messages'],
        'language': state['language'],
        'summary': state.get('summary', '')
    })
    return {"messages": [response]}


def should_continue(state: State) -> Literal["summarize_conversation", END]:
    """Return the next node to execute."""
    messages = state["messages"]
    if len(messages) > 6:
        return "summarize_conversation"

    return END


def summarize_conversation(state: State):
    # First, we summarize the conversation
    summary = state.get("summary", "")
    if summary:
        # If a summary already exists, we use a different system prompt
        # to summarize it than if one didn't
        summary_message = (
            f"当前对话的总结是: {summary}\n\n"
            "使用如下消息，扩展上述的对话总结："
        )
    else:
        summary_message = "生成对上述对话的总结："

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    # 保留最新的一组对话，其余的从列表删除
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


workflow = StateGraph(State)

workflow.add_node("conversation", call_model)
workflow.add_node(summarize_conversation)

workflow.add_edge(START, "conversation")
# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `conversation`.
    # This means these are the edges taken after the `conversation` node is called.
    "conversation",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)

# We now add a normal edge from `summarize_conversation` to END.
# This means that after `summarize_conversation` is called, we end.
workflow.add_edge("summarize_conversation", END)

# Finally, we compile it!
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

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
    language = st.sidebar.selectbox("选择语言：", ["汉语", "英语"])

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