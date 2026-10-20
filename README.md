# Customer Complaint Handling AI Agent (MVP)

A beginner-friendly Streamlit app with one CrewAI agent, RAG over an uploaded Knowledge Transfer (KT) document, and session-only short-term chat memory.

## MVP features
- Upload one PDF, TXT, Markdown, or DOCX KT document.
- Extract text and retrieve relevant passages using Sentence Transformers + FAISS.
- Ask conversational questions about complaint handling.
- Generate guidance through one CrewAI agent using Groq.
- Show retrieved KT source labels.
- Keep recent chat history in the active Streamlit session.
- No database connection, SQL execution, automatic ticket updates, or intentional database storage.

## Important limitations
- The MVP uses text extraction. Scanned PDFs, screenshots, and diagrams may require OCR/image extraction before they can be searched.
- Optional web search is not enabled by default. This is deliberate for privacy and source-control.
- The first use of Sentence Transformers downloads its embedding model; this can increase startup time and memory use on Streamlit Community Cloud.
- Do not upload confidential customer records unless your organization approves the use of the hosting and model providers. The prompt/context sent to Groq is processed by that provider according to its terms.
- RAG retrieval is not guaranteed to find every relevant passage. Validate answers against the KT before operational use.

## 1. Create the GitHub repository
Create a new repository, for example `customer-complaint-agent`, and upload all files/folders from this project. Do not upload a real `.streamlit/secrets.toml`.

## 2. Configure Groq
1. Create or access your Groq API key through the official Groq console.
2. In Streamlit Community Cloud, deploy this repository.
3. Open the app's **Settings → Secrets** and add:

```toml
GROQ_API_KEY = "your_real_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-20b"
```

Check the Groq console for currently available models and access. If this model is not available to your account, replace `GROQ_MODEL` with a currently supported chat model from your Groq console.

## 3. Deploy on Streamlit Community Cloud
1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose **Create app** and select your repository.
3. Set the main file path to `app.py`.
4. Deploy, then add the Secrets shown above.
5. Reboot the app if prompted.

## 4. Use the app
1. Upload your approved KT document in the left sidebar.
2. Wait for the knowledge base to finish processing.
3. Paste a sanitized ticket description or ask a procedure question.
4. Review the response and the KT references.
5. If the KT does not answer the question, provide the relevant approved section or ask your team lead.

## Local run (optional)
If you have Python and a terminal available:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Privacy and security
- Never commit API keys to GitHub.
- `.streamlit/secrets.toml` is ignored by Git.
- Avoid customer names, phone numbers, IMSIs, credentials, and other personal/confidential information in test tickets.
- Chat history is kept in Streamlit session state only; it is not intentionally written to a database by this app. Hosting logs and model-provider processing are separate considerations.
- Use organization-approved hosting, data retention, and AI-provider settings before production use.

## Suggested acceptance tests
- Ask a procedure question clearly answered by the KT.
- Ask a follow-up question that depends on the previous message.
- Ask about a procedure absent from the KT and verify that the agent admits uncertainty.
- Upload a scanned PDF and verify that the app warns about missing selectable text.
- Test with synthetic tickets before using real complaint data.
