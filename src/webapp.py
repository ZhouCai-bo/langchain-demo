import logging
import time
import random

import streamlit as st


st.title("Chat with LLMs Models")  # Set the title of the Streamlit app

if 'messages' not in st.session_state:
    st.session_state.messages = []

def stream_chat(model, messages):
    time.sleep(random.randint(0, 3))
    return 'test message'
    try:
        # Initialize the language model with a timeout
        llm = Ollama(model=model, request_timeout=120.0) 
        # Stream chat responses from the model
        resp = llm.stream_chat(messages)
        response = ""
        response_placeholder = st.empty()
        # Append each piece of the response to the output
        for r in resp:
            response += r.delta
            response_placeholder.write(response)
        # Log the interaction details
        logging.info(f"Model: {model}, Messages: {messages}, Response: {response}")
        return response
    except Exception as e:
        # Log and re-raise any errors that occur
        logging.error(f"Error during streaming: {str(e)}")
        raise e


def draw():
    #defining side bar
    st.sidebar.header("Filters:")

    name = st.sidebar.text_input(label='千帆AK：')
    passwd = st.sidebar.text_input(label='千帆SK：', type="password")

    # Sidebar for model selection
    model = st.sidebar.selectbox("Choose a model", ["百度千帆"])

    # Prompt for user input and save to chat history
    if prompt := st.chat_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display the user's query
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Generate a new response if the last message is not from the assistant
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                start_time = time.time()  # Start timing the response generation

                with st.spinner("Writing..."):
                    try:
                        # Prepare messages for the LLM and stream the response
                        # messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in st.session_state.messages]
                        messages = [st.session_state.messages]
                        response_message = stream_chat(model, messages)
                        duration = time.time() - start_time  # Calculate the duration
                        response_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                        st.session_state.messages.append({"role": "assistant", "content": response_message_with_duration})
                        st.write(response_message_with_duration)
                        # st.write(f"Duration: {duration:.2f} seconds")
                        logging.info(f"Response: {response_message}, Duration: {duration:.2f} s")

                    except Exception as e:
                        # Handle errors and display an error message
                        st.session_state.messages.append({"role": "assistant", "content": str(e)})
                        st.error("An error occurred while generating the response.")
                        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    draw()