import os
import streamlit as st

SYSTEM_RULES = """
You are a single customer complaint-handling assistant mentoring a newly joined telecom operations team member.
Be calm, clear, concise, and practical. Guide the user step by step.

Source policy:
- The supplied internal KT context is the primary source of truth for internal complaint procedures.
- Do not invent application steps, SQL commands, database changes, workarounds, escalation groups, or closure criteria.
- If the KT context does not answer the question, explicitly say the available KT excerpt does not establish the answer and ask for the relevant KT section or recommend confirming with the authorized team lead.
- If external/web information is supplied separately, label it as external and never let it override internal KT.
- Distinguish confirmed KT facts from suggestions.
- If the question is missing key ticket details, ask a short clarifying question.
- Never request passwords, API keys, or unnecessary customer personal data.
- Do not execute actions. This app is guidance-only and has no production-system access.

Preferred response structure when appropriate:
1. What the ticket indicates
2. Checks to perform
3. Decision / next step
4. Escalation or closure criteria
5. KT source (document/page/section if available)
Avoid forcing this structure for simple follow-up questions.
"""

def _get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

def answer_complaint(question, context, history):
    """Generate a KT-grounded answer with CrewAI; fall back to direct Groq API if needed."""
    api_key = _get_secret("GROQ_API_KEY")
    model = _get_secret("GROQ_MODEL", "openai/gpt-oss-20b")
    if not api_key:
        return (
            "Your question is received, but the Groq API key is not configured yet.\n\n"
            "To enable AI answers, add `GROQ_API_KEY` in Streamlit Cloud → App settings → Secrets. "
            "See README.md for instructions. Your uploaded KT can still be processed locally by this app."
        ), []

    history_text = "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}"
        for m in history[-8:]
    )
    user_prompt = f"""
RECENT CONVERSATION:
{history_text}

RETRIEVED INTERNAL KT CONTEXT:
{context if context else "[No KT document has been uploaded or no relevant passages were found. Do not claim the answer is KT-backed.]"}

CURRENT QUESTION:
{question}

Answer using the source policy. When relevant, refer to the KT source labels included in the context.
"""
    # CrewAI path: one agent, no autonomous external actions or database tools.
    try:
        from crewai import Agent, Task, Crew, LLM
        llm = LLM(model=f"groq/{model}", api_key=api_key, temperature=0.1)
        agent = Agent(
            role="Customer Complaint Handling Mentor",
            goal="Give safe, accurate, source-grounded guidance for handling customer complaint tickets",
            backstory="An experienced telecom operations mentor who follows approved KT documents and never invents procedures.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=f"{SYSTEM_RULES}\n\n{user_prompt}",
            expected_output="A clear, concise, actionable answer grounded in the supplied KT context, with uncertainty stated honestly.",
            agent=agent,
        )
        result = Crew(agents=[agent], tasks=[task], verbose=False).kickoff()
        answer = str(result)
    except Exception as crew_error:
        # Fallback keeps the MVP usable if CrewAI's Groq adapter changes.
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_RULES},
                    {"role": "user", "content": user_prompt},
                ],
            )
            answer = completion.choices[0].message.content or "No answer was returned."
        except Exception as api_error:
            raise RuntimeError(f"CrewAI error: {crew_error}; Groq API error: {api_error}") from api_error

    sources = []
    for line in (context or "").splitlines():
        if line.startswith("[Source:"):
            label = line.split("]", 1)[0].replace("[Source:", "").strip()
            if label and label not in sources:
                sources.append(label)
    return answer, sources
