# Customer Complaint Handling Agent

This repository contains a modular single-agent Streamlit application built with CrewAI, RAG (PDF search), and external Web Search capabilities.

## Structure
- `app.py`: Streamlit frontend UI & session memory handling.
- `agent_core.py`: CrewAI agent logic, RAG tool, and web search integration.
- `requirements.txt`: Python package dependencies.

## Setup Instructions

1. Extract the ZIP file and navigate to the project directory:
   ```bash
   cd customer_complaint_agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
