import streamlit as st
from pathlib import Path
from knowledge_base import build_knowledge_base, retrieve_context
from agent import answer_complaint
from memory import add_message, get_history, clear_history

st.set_page_config(page_title="Customer Complaint Handling Agent", page_icon="🎧", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; max-width: 1150px;}
.hero {padding: 1.25rem 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#10243a,#205b70); color: white; margin-bottom: 1rem;}
.hero h1 {margin:0; font-size: 2rem;}
.hero p {margin:.4rem 0 0 0; color:#e7f2f6;}
.small-note {color: #64748b; font-size: .9rem;}
div[data-testid="stChatMessage"] {border-radius: 12px;}
</style>
<div class="hero">
<h1>🎧 Customer Complaint Handling Agent</h1>
<p>Practical, KT-grounded guidance for ticket investigation, troubleshooting and escalation.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Knowledge base")
    st.write("Upload your approved Knowledge Transfer (KT) document to ground answers in your team's procedures.")
    uploaded = st.file_uploader("Upload KT document", type=["pdf", "txt", "md", "docx"], help="For the MVP, upload one document at a time.")
    st.caption("PDF text is supported. Scanned PDFs and screenshots may need OCR before their content can be retrieved.")
    if uploaded is not None:
        st.session_state["uploaded_bytes"] = uploaded.getvalue()
        st.session_state["uploaded_name"] = uploaded.name
        st.session_state.pop("kb_chunks", None)
        st.success(f"Loaded: {uploaded.name}")
    if st.button("Clear conversation", use_container_width=True):
        clear_history()
        st.rerun()
    st.divider()
    st.caption("MVP safety: guidance only. No database connection, SQL execution, or ticket updates.")

if "kb_chunks" not in st.session_state:
    st.session_state["kb_chunks"] = []
    st.session_state["kb_name"] = None

if st.session_state.get("uploaded_bytes"):
    if not st.session_state["kb_chunks"]:
        with st.spinner("Processing KT document..."):
            try:
                chunks, name = build_knowledge_base(
                    st.session_state["uploaded_bytes"],
                    st.session_state["uploaded_name"]
                )
                st.session_state["kb_chunks"] = chunks
                st.session_state["kb_name"] = name
                st.success(f"Knowledge base ready: {len(chunks)} text sections.")
            except Exception as e:
                st.error(f"Could not process this document: {e}")
else:
    st.info("Start by uploading your KT document in the left panel. You can also ask general questions, but answers without KT may be limited.")

st.markdown("### Complaint workspace")
with st.expander("Enter ticket details (optional)", expanded=False):
    ticket_id = st.text_input("Ticket/reference ID (avoid confidential identifiers)", placeholder="e.g., CCD-12345")
    complaint_type = st.text_input("Complaint type", placeholder="e.g., Activation date missing")
    ticket_description = st.text_area("Ticket description", placeholder="Paste a sanitized ticket description. Remove customer names, phone numbers, IMSI and other sensitive data.", height=120)
    if st.button("Add ticket details to chat"):
        parts = []
        if ticket_id.strip(): parts.append(f"Ticket reference: {ticket_id.strip()}")
        if complaint_type.strip(): parts.append(f"Complaint type: {complaint_type.strip()}")
        if ticket_description.strip(): parts.append(f"Ticket description: {ticket_description.strip()}")
        if parts:
            add_message("user", "Please help me handle this ticket using the KT.\n" + "\n".join(parts))
            st.rerun()

history = get_history()
for msg in history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask how to investigate, resolve, escalate or close a complaint...")
if prompt:
    add_message("user", prompt)
    chunks = st.session_state.get("kb_chunks", [])
    context = retrieve_context(prompt, chunks) if chunks else ""
    history_for_llm = get_history()[-10:]
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Reviewing the KT and preparing guidance..."):
            try:
                response, sources = answer_complaint(prompt, context, history_for_llm)
            except Exception as e:
                response = f"Sorry, I couldn't generate an answer. Check your Groq API key and model configuration. Technical detail: {e}"
                sources = []
        st.markdown(response)
        if sources:
            with st.expander("KT references used"):
                for source in sources:
                    st.markdown(f"- {source}")
    add_message("assistant", response)
    if sources:
        add_message("assistant", "\n**KT references used:**\n" + "\n".join(f"- {s}" for s in sources))

st.divider()
st.markdown('<p class="small-note">Privacy note: conversation memory is kept in the active Streamlit session. This app does not intentionally save uploaded documents or chats to a database. The LLM provider receives the prompt/context sent for answer generation; use only organization-approved, sanitized data.</p>', unsafe_allow_html=True)
