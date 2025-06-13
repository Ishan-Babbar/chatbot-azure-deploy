✅ PHASE 1: Local Development & Core Functionality
🔹 1. PDF-Based RAG Chatbot (Complete)
Ingested PDFs from a local folder
Chunked and embedded text
Used Azure OpenAI (gpt-4o-mini-voc2) for answering questions
✅ PHASE 2: LLMOps & Productionization
🔹 2. Prompt Versioning (Complete)
Created prompts/v1_prompt.json with CoT, ToT, GoT, strict, and default strategies
Refactored build_prompt() to load from JSON
Enabled version tracking for prompts and models
🔹 3. Structured Logging (Complete)
Added utils/logger.py using loguru
Logs user query, strategy, prompt version, model, response, and errors
🔹 4. Feedback Loop (Complete)
Created utils/feedback_logger.py
Captures thumbs up/down feedback to feedback/feedback_log.csv
Integrated into CLI flow in chat_code.py
🔹 5. CI/CD & Deployment (In Progress)
Created .github/workflows/deploy.yml for GitHub Actions
Configured deployment to Azure App Service
You need to:
Add secrets to GitHub (AZURE_WEBAPP_NAME, AZURE_WEBAPP_PUBLISH_PROFILE)
Push to main to trigger deployment
🛠️ PHASE 3: What’s Next
🔜 6. Observability Dashboard
Option 1: Local dashboard (e.g., Streamlit, Power BI)
Option 2: Azure Monitor integration
Purpose: Visualize usage, feedback trends, token costs, etc.
🔜 7. Security & Governance
Add PII redaction in logs
Encrypt sensitive data
Add user consent if storing chat history
Optional: Azure AD authentication