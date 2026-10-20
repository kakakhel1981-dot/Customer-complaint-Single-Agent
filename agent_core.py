import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

load_dotenv()

def run_complaint_agent(uploaded_file_path: str, user_query: str, chat_history: list = None) -> str:
    """
    Initializes the CrewAI agent with PDF RAG and Web Search capabilities,
    then executes the task based on the user query and chat history.
    """
    # 1. Initialize Tools
    pdf_tool = PDFSearchTool(pdf=uploaded_file_path)
    search_tool = SerperDevTool()
    
    # 2. Define the Single Agent
    complaint_agent = Agent(
        role='Customer Support Specialist',
        goal='Accurately answer customer complaints and questions using the uploaded KT (Knowledge Transfer) document.',
        backstory=(
            "You are an expert customer support agent equipped with company Knowledge Transfer documents. "
            "Always prioritize facts and instructions found in the KT document first. "
            "If brief external or supplementary context is required to handle the query completely, use the web search tool."
        ),
        tools=[pdf_tool, search_tool],
        verbose=True,
        memory=True
    )
    
    # 3. Format Short-Term Conversation History
    history_context = ""
    if chat_history:
        # Keep the last 4 turns for context
        recent_messages = chat_history[-4:]
        history_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages])
        
    # 4. Define the Task
    task_description = f"""
    Handle the customer complaint or question below. 
    Rely primarily on the uploaded KT document.
    
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
