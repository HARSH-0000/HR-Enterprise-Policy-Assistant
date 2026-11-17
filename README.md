# HR Enterprise Policy Assistant

An AI-powered HR policy assistant that helps employees find answers to company-policy questions through a conversational interface. It uses a Corrective Retrieval-Augmented Generation (CRAG) workflow to retrieve relevant HR policy content, evaluate its relevance, and verify that generated answers are supported by approved documents.

## Overview

Employees often need to search lengthy HR documents to understand policies related to leave, benefits, attendance, workplace guidelines, and other internal processes. This project provides a single chat interface for asking those questions in natural language.

The assistant is designed to answer from indexed HR policy documents rather than relying only on the language model's general knowledge. If it cannot find sufficient approved evidence, it responds with a fallback directing the employee to HR.

## Key Features

- **Conversational HR Q&A:** Ask questions about company policies using natural language.
- **Corrective RAG (CRAG):** Retrieve, grade, and refine document retrieval when the initial results are not relevant.
- **Approved-document filtering:** Only documents marked with an `approved` status are eligible for answer generation.
- **Reranking:** Reorder retrieved passages to prioritize the most relevant context.
- **Grounding verification:** Check whether the generated answer is supported by the retrieved policy context.
- **Source metadata:** Return policy title, policy ID, page, department, section, version, and effective date when available.
- **PDF ingestion pipeline:** Load HR policy documents, split them into chunks, generate embeddings, and index them in Pinecone.
- **Web interface:** React and TypeScript frontend for interacting with the assistant.
- **Container configuration:** Dockerfiles and Docker Compose configuration for the frontend and backend services.

## Architecture

```text
                  Employee
                     |
                     v
          React + TypeScript Frontend
                     |
                 HTTP /chat
                     |
                     v
              FastAPI Backend
                     |
                     v
           LangGraph CRAG Workflow
                     |
          +----------+-----------+
          |          |           |
          v          v           v
       Retrieve    Grade       Rerank
          |       Documents   Results
          |          |
          +----------+
                     |
          Relevant documents found?
               /           \
             No             Yes
             |               |
       Rewrite query         v
             |          Generate answer
             |               |
             +----> Retrieve v
                       Verify grounding
                             |
                             v
                  Answer + policy sources
                             |
                             v
                      Frontend UI


     HR Policy PDFs
           |
           v
    Document Ingestion
           |
    Extract text and split
           |
    Sentence Transformers
           |
           v
      Pinecone Vector DB
           |
       Retrieval
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend API | Python, FastAPI, Uvicorn, Pydantic |
| LLM | Groq API, configurable through `GROQ_MODEL` |
| Orchestration | LangChain, LangGraph |
| RAG | Corrective RAG (CRAG), document relevance grading, query rewriting, grounding verification |
| Embeddings | Hugging Face Sentence Transformers, `all-MiniLM-L6-v2` |
| Vector database | Pinecone |
| Document processing | PyPDF |
| Deployment | Docker, Docker Compose, Nginx |

## Project Structure

```text
HR-Enterprise-Policy-Assistant/
├── backend/
│   ├── app/
│   │   ├── core/              # Application configuration
│   │   ├── rag/               # CRAG graph, prompts, embeddings,
│   │   │                      # reranking, and vector store
│   │   ├── schemas/           # Request and response models
│   │   ├── services/          # Chat orchestration service
│   │   └── main.py            # FastAPI application and endpoints
│   ├── data/
│   │   └── hr_policies/       # Place HR policy documents here
│   ├── scripts/
│   │   └── ingest_policies.py # Policy ingestion and indexing
│   ├── .env.example           # Backend environment template
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── services/          # Backend API client
│   │   ├── constants/
│   │   ├── types/
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## How It Works

1. **Policy ingestion:** HR policy PDFs are loaded from `backend/data/hr_policies/`.
2. **Text extraction and chunking:** The ingestion script extracts document text and divides it into smaller passages.
3. **Embedding generation:** The Hugging Face embedding model converts each passage into a vector representation.
4. **Vector indexing:** The vectors and associated metadata are stored in the configured Pinecone index and namespace.
5. **Retrieval:** When an employee asks a question, the backend retrieves the most similar policy passages.
6. **Relevance grading:** The LangGraph workflow evaluates the retrieved passages. If no relevant approved documents are found, it can rewrite the search query and retry according to the configured retry limit.
7. **Answer generation:** The LLM generates an answer using the retrieved policy context.
8. **Grounding verification:** The workflow checks whether the answer is supported by the policy context. Unsupported answers are replaced with a safe fallback.
9. **Response:** The API returns the answer, grounding status, and available policy-source metadata to the frontend.

## Getting Started

### Prerequisites

- Python 3.12
- Node.js and npm
- A Groq API key
- A Pinecone account and API key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/HARSH-0000/HR-Enterprise-Policy-Assistant.git
cd HR-Enterprise-Policy-Assistant
```

### 2. Configure the backend

Create a virtual environment and install the Python dependencies.

**Windows PowerShell:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `backend/.env` and provide your credentials:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL="openai/gpt-oss-120b"

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=hr-enterprise-assistant
PINECONE_NAMESPACE=company-policies

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

RETRIEVAL_K=8
MAX_RETRIES=1

CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

Use a Groq model available to your account. Never commit your actual API keys or the `.env` file.

### 3. Add and index HR policies

Place the HR policy PDF files in:

```text
backend/data/hr_policies/
```

Activate the backend virtual environment, make sure the Groq and Pinecone settings are configured, and run the ingestion script from the `backend` directory:

```bash
python scripts/ingest_policies.py
```

The ingestion script processes the policy documents and stores their embeddings in the configured Pinecone index and namespace. Review the ingestion script before running it against an existing index: its current initialization logic deletes and recreates the configured Pinecone index.

**Important:** Documents must carry the expected approval metadata to be eligible for retrieval by the CRAG workflow. The workflow filters for documents whose `status` metadata is `approved`.

### 4. Start the backend

Run from the `backend` directory with the virtual environment activated:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/chat` | Ask an HR policy question |

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

Example chat request:

```json
{
  "query": "How many days of annual leave are available to employees?"
}
```

The response includes the generated answer, source metadata, grounding flag, and response status.

### 5. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local Vite URL shown in the terminal, normally:

```text
http://localhost:5173
```

Make sure the backend is running and that its CORS configuration allows the frontend origin.

## Run with Docker Compose

Docker Compose configuration is included for running the backend and frontend containers together.

1. Create `backend/.env` using `backend/.env.example` and add valid API credentials.
2. Add policy PDFs under `backend/data/hr_policies/` and complete the Pinecone ingestion step.
3. From the repository root, build and start the services:

```bash
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

The Compose configuration maps the backend to port `8000` and the frontend to port `80` (also mapped to `5173`). The backend health endpoint is used as the frontend startup dependency check.

## API

### `GET /health`

Checks whether the API process is responding.

Example response:

```json
{
  "status": "ok",
  "service": "hr-enterprise-assistant"
}
```

### `POST /chat`

Request:

```json
{
  "query": "What is the company's work-from-home policy?"
}
```

The response schema contains:

- `response`: assistant answer.
- `sources`: list of policy source metadata.
- `grounded`: whether the answer passed the grounding check.
- `status`: processing outcome, such as `answered`, `insufficient_evidence`, or `ungrounded`.

## Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | API key for Groq |
| `GROQ_MODEL` | Groq chat model name |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX` | Pinecone index name |
| `PINECONE_NAMESPACE` | Namespace used for HR policy vectors |
| `EMBEDDING_MODEL` | Hugging Face embedding model |
| `RETRIEVAL_K` | Number of documents initially retrieved |
| `MAX_RETRIES` | Maximum query-rewrite retries |
| `CORS_ORIGINS` | Comma-separated frontend origins allowed by the API |

## Responsible Use

- The assistant should be used as a policy-information aid, not as a replacement for an official HR decision.
- Answers depend on the accuracy, completeness, approval status, and freshness of the indexed policy documents.
- If the assistant cannot find approved supporting evidence, employees should contact the HR department.
- Do not upload confidential employee records or personally identifiable information unless the deployment has been explicitly reviewed and approved for that data.
- Keep API credentials in environment variables and restrict access to policy documents and vector database resources.

## Current Scope

The current implementation focuses on question answering over approved HR policy documents. It includes a CRAG retrieval and verification workflow, a FastAPI chat API, a React frontend, and a PDF ingestion pipeline. Employee-specific HR transactions and integrations with enterprise HR systems are outside the current policy-Q&A scope.

## Future Enhancements

- Role-based access control and employee authentication.
- Employee-specific policy responses with appropriate authorization.
- Admin interface for policy upload, approval, versioning, and re-indexing.
- Conversation history and feedback collection.
- Automated evaluation for retrieval quality, answer faithfulness, and citation accuracy.
- Monitoring, audit logging, and production deployment hardening.

## License

No license has been specified for this repository yet. Add a `LICENSE` file before distributing or reusing the project under an open-source license.
