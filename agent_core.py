import os
import asyncio
import nest_asyncio

# Apply nest_asyncio patch to fix Streamlit threading loop issues
nest_asyncio.apply()

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

load_dotenv()

def run_complaint_agent(uploaded_file_path: str, user_query: str, chat_history: list = None) -> str:
    """
    Initializes the CrewAI agent with PDF RAG and Web Search capabilities,
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

    # Explicitly configure modern LLM to prevent legacy fallback errors (APIRemovedInV1)
 openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError(
        "OPENAI_API_KEY is missing. "
        "Add it in Streamlit Cloud → Settings → Secrets."
    )

my_llm = LLM(
    model="openai/gpt-4o-mini",
    api_key=openai_api_key,
    temperature=0.2,
    timeout=120,
)
    # 1. Initialize Tools
    pdf_tool = PDFSearchTool(pdf=uploaded_file_path)
    search_tool = SerperDevTool()
    
    # 2. Define the Single Agent with explicit modern LLM
    complaint_agent = Agent(
        role='Customer Support Specialist',
        goal='Accurately answer customer complaints and questions using the uploaded KT (Knowledge Transfer) document.',
        backstory=(
            "You are an expert customer support agent equipped with company Knowledge Transfer documents. "
            "Always prioritize facts and instructions found in the KT document first. "
            "If brief external or supplementary context is required to handle the query completely, use the web search tool."
        ),
        tools=[pdf_tool, search_tool],
        llm=my_llm,
        verbose=True,
        memory=True
    )
    
    # 3. Format Short-Term Conversation History
    history_context = ""
    if chat_history:
        recent_messages = chat_history[-4:]
        history_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])
        
    # 4. Define the Task
    task_description = f"""
    Handle the customer complaint or question below. 
    Rely primarily on the KT document.
    
    Recent Conversation History:
    {history_context}
    
    Current Customer Query/Complaint: {user_query}
    """
    
    complaint_task = Task(
        description=task_description,
        expected_output="A helpful, professional, and accurate response addressing the customer's issue based on the KT document guidelines.",
        agent=complaint_agent
    )
    
    # 5. Create and Run the Crew
    crew = Crew(
        agents=[complaint_agent],
        tasks=[complaint_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return str(result)
