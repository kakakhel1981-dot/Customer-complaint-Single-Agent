import streamlit as st
import os
import tempfile
from agent_core import run_complaint_agent

# Page Configuration
st.set_page_config(
    page_title="Customer Complaint AI Agent",
    page_icon="🛡️",
    layout="centered"
)

st.title("🛡️ Customer Complaint Handling Assistant")
st.markdown("Upload your Knowledge Transfer (KT) PDF document below and chat with the AI agent to resolve customer complaints.")

# Sidebar Configuration
with st.sidebar:
    st.header("🔑 API Credentials")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    serper_api_key = st.text_input("Serper API Key (Web Search)", type="password")
    
    st.markdown("---")
    st.header("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Upload KT Document (PDF)", type=["pdf"])
    
    # Set environment variables dynamically if provided
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    if serper_api_key:
        os.environ["SERPER_API_KEY"] = serper_api_key

# Initialize Short-Term Memory (Streamlit Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat history on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Handling
if prompt := st.chat_input("Enter customer complaint or query here..."):
    # Validation checks
    if not uploaded_file:
        st.warning("⚠️ Please upload a KT PDF document in the sidebar first!")
    elif not os.environ.get("OPENAI_API_KEY"):
        st.warning("⚠️ Please enter your OpenAI API Key in the sidebar to proceed!")
    else:
        # Save the uploaded file temporarily so tools can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Append user message to memory
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Agent Response
        with st.chat_message("assistant"):
            with st.spinner("Agent is analyzing the KT document and formulating a response..."):
                try:
                    response = run_complaint_agent(
                        uploaded_file_path=tmp_path,
                        user_query=prompt,
                        chat_history=st.session_state.messages
                    )
                    st.markdown(response)
                    # Append assistant response to memory
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"An error occurred during execution: {e}")
                finally:
                    # Clean up temporary file safely
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
