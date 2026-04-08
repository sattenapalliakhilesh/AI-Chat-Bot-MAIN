# AI Chat Bot — Document Q&A with RAG

A web-based chatbot that lets you upload documents (PDF or plain text) and ask questions about them using Claude AI. It uses Retrieval-Augmented Generation (RAG) with ChromaDB vector search to provide accurate, context-aware answers grounded in your document's content.

## Features

- **PDF & Text Upload** — Upload `.pdf` files or paste plain text directly
- **Semantic Search** — ChromaDB vector store finds the most relevant document sections per query
- **Multi-turn Chat** — Conversation history is maintained within your session
- **Session Isolation** — Each browser session gets its own document store and chat history
- **Reset / New Document** — Clear everything and start fresh without reloading the page
- **Responsive UI** — Works on desktop and mobile browsers

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI Model | Anthropic Claude (`claude-opus-4-5`) |
| Vector Store | ChromaDB (in-memory) |
| PDF Parsing | PyPDF2 |
| Config | python-dotenv |

## Architecture

```
Browser (index.html)
       │
  Flask (app.py)
  ├── GET  /          → Serve UI, assign session ID
  ├── POST /upload    → Extract text → chunk → store in ChromaDB
  ├── POST /chat      → Retrieve top-3 chunks → call Claude API → return answer
  └── POST /reset     → Clear ChromaDB collection + session history
       │
  External Services
  ├── Anthropic Claude API
  └── ChromaDB (in-memory vector database)
```

## Getting Started

### Prerequisites

- Python 3.12+
- An [Anthropic API key](https://console.anthropic.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/sattenapalliakhilesh/ai-chat-bot.git
cd ai-chat-bot

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install flask anthropic PyPDF2 chromadb python-dotenv
```

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

### Run

```bash
python app.py
```

Open your browser at `http://localhost:5000`.

## Usage

1. **Upload a document** — drag and drop a PDF onto the sidebar, or paste text into the text area and click **Upload Text**.
2. **Ask questions** — type your question in the chat input and press **Enter** (or **Shift+Enter** for a new line).
3. **Start over** — click **Reset** to clear the document and chat history.

## Project Structure

```
AI-Chat-Bot/
├── app.py              # Flask backend — routes, RAG logic, Claude API calls
├── templates/
│   └── index.html      # Single-page frontend
├── .env                # API key (not committed)
└── README.md
```

## Notes

- Document embeddings and chat history are stored **in memory** and are lost when the server restarts.
- Scanned PDFs (image-based) are not supported — only text-based PDFs work.
- Each chat query incurs Anthropic API usage costs.
- The app runs in Flask's development mode by default (`debug=True`). Set `debug=False` for production.

## License

MIT
