import os
import secrets
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import chromadb

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)
client = Anthropic()
chroma_client = chromadb.Client()
conversation_store = {}

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks

def get_embedding(text):
    response = client.beta.messages.batches
    result = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1,
        system="Return nothing.",
        messages=[{"role": "user", "content": text}]
    )
    return None

def store_document(session_id, text):
    collection_name = f"doc_{session_id}"

    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass

    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    chunks = chunk_text(text)

    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    print(f"Stored {len(chunks)} chunks for session {session_id}")
    return len(chunks)

def get_relevant_chunks(session_id, question, n_results=3):
    collection_name = f"doc_{session_id}"

    try:
        collection = chroma_client.get_collection(collection_name)
    except:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, collection.count())
    )

    return results["documents"][0] if results["documents"] else []

@app.route("/")
def index():
    session_id = secrets.token_hex(16)
    session["session_id"] = session_id
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Session expired. Please refresh the page."})

    text = ""

    if "pdf_file" in request.files and request.files["pdf_file"].filename != "":
        file = request.files["pdf_file"]
        if not file.filename.endswith(".pdf"):
            return jsonify({"error": "Please upload a valid PDF file."})
        text = extract_text_from_pdf(file)

    elif request.form.get("doc_text", "").strip():
        text = request.form.get("doc_text", "").strip()

    else:
        return jsonify({"error": "Please paste text or upload a PDF first."})

    if len(text.strip()) < 50:
        return jsonify({"error": "Document is too short. Please provide more content."})

    num_chunks = store_document(session_id, text)
    conversation_store[session_id] = []

    return jsonify({
        "success": True,
        "preview": text[:200] + "...",
        "chunks": num_chunks
    })

@app.route("/chat", methods=["POST"])
def chat():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Please upload a document first."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Please type a message."})

    relevant_chunks = get_relevant_chunks(session_id, user_message)

    if not relevant_chunks:
        return jsonify({"error": "No document found. Please upload a document first."})

    context = "\n\n---\n\n".join(relevant_chunks)
    messages = conversation_store.get(session_id, [])
    messages.append({"role": "user", "content": user_message})

    system_prompt = f"""You are a helpful assistant that answers questions strictly based on the document excerpts below.

Rules:
- Only answer using information from the excerpts
- If the answer is not in the excerpts, say "I couldn't find that in the document."
- Be concise and clear
- Quote relevant parts when helpful

Relevant excerpts:
{context}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )

    assistant_message = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_message})
    conversation_store[session_id] = messages

    return jsonify({
        "response": assistant_message,
        "chunks_used": len(relevant_chunks)
    })

@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.get("session_id")
    if session_id:
        try:
            chroma_client.delete_collection(f"doc_{session_id}")
        except:
            pass
        conversation_store.pop(session_id, None)
    session.clear()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)