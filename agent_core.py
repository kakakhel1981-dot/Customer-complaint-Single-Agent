import os
import asyncio
import nest_asyncio
import fitz  # PyMuPDF

# Apply nest_asyncio patch to fix Streamlit threading loop issues
nest_asyncio.apply()

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

load_dotenv()

def extract_pdf_text(pdf_path: str) -> str:
    """Extracts all text cleanly from the uploaded PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        text = f"Error reading PDF: {str(e)}"
    return text

def run_complaint_agent(uploaded_file_path: str, user_query: str, chat_history: list = None) -> str:
    """
    Initializes the CrewAI agent with direct PDF text and Web Search capabilities,
    then executes the task based on the user query and chat history.
    """
    # Ensure event loop exists for safety
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Use the active, high-speed Groq model
    my_llm = LLM(
        model="groq/openai/gpt-oss-120b",
        temperature=0.2
    )

    # 1. Extract PDF text directly
    kt_document_text = extract_pdf_text(uploaded_file_path)

    # 2. Initialize Web Search Tool
    search_tool = SerperDevTool()
    
    # 3. Define the Single Agent
    complaint_agent = Agent(
        role='Customer Support Specialist',
        goal='Accurately answer customer complaints and questions using the provided Knowledge Transfer (KT) document text.',
        backstory=(
            "You are an expert customer support agent equipped with company Knowledge Transfer documents. "
            "Always prioritize facts and instructions found in the KT document text first. "
            "If brief external or supplementary context is required to handle the query completely, use the web search tool."
        ),
        tools=[search_tool],
        llm=my_llm,
        verbose=True,
        memory=True
    )
    
    # 4. Format Short-Term Conversation History
    history_context = ""
    if chat_history:
        recent_messages = chat_history[-4:]
        history_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])
        
    # 5. Define the Task embedding the KT document text directly
    task_description = f"""
    Handle the customer complaint or question below. 
    Rely primarily on the Knowledge Transfer (KT) document text provided below.
    
    --- KNOWLEDGE TRANSFER DOCUMENT START ---
    {kt_document_text[:15000]}
    --- KNOWLEDGE TRANSFER DOCUMENT END ---
    
    Recent Conversation History:
    {history_context}
    
    Current Customer Query/Complaint: {user_query}
    """
    
    complaint_task = Task(
        description=task_description,
        expected_output="A helpful, professional, and accurate response addressing the customer's issue based on the KT document guidelines.",
        agent=complaint_agent
    )
    
    # 6. Create and Run the Crew
    crew = Crew(
        agents=[complaint_agent],
        tasks=[complaint_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return str(result)
