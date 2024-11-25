from typing import Sequence
from typing_extensions import Annotated, TypedDict

from langchain.chat_models import QianfanChatEndpoint
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.message import add_message
from langchain_core import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, trim_messages


ak = 'MSh0vo1NQTErNMBGlcnODVvi'
sk = '3Yhn7t0JZmUj6Zf2S0g4veuPARevlCOv'


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

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_message]
    language: str

workflow = StateGraph(state_schema=State)

trimmer = trim_messages(
    max_tokens=65,
    strategy='last',
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on='human',
)

def call_model(state: State, messages: list[BaseMessage]=None):
    chain = prompt | model
    if not messages:
        trimmed_messages = trimmer.invoke(state['messages'])
    else:
        trimmed_messages = trimmer.invoke(messages)
    response = chain.invoke({
        'messages': trimmed_messages,
        'language': state['language']
    })
    return {'messages': [response]}


workflow.add_edge(START, 'mode')
workflow.add_node('model', call_model)

memory = MemorySaver()
app = workflow.compile(checkpoint=memory)