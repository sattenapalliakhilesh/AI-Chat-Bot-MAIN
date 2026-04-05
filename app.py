import os
import secrets
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)
client = Anthropic()

document_store = {}
conversation_store = {}

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

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

    document_store[session_id] = text[:20000]
    conversation_store[session_id] = []

    print(f"Document saved for session {session_id}, length: {len(text)}")
    return jsonify({"success": True, "preview": text[:200] + "..."})

@app.route("/chat", methods=["POST"])
def chat():
    session_id = session.get("session_id")
    if not session_id or session_id not in document_store:
        return jsonify({"error": "Please upload a document first."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Please type a message."})

    document = document_store[session_id]
    messages = conversation_store.get(session_id, [])

    messages.append({"role": "user", "content": user_message})

    system_prompt = f"""You are a helpful assistant that answers questions strictly based on the document provided below.

Rules:
- Only answer using information from the document
- If the answer is not in the document, say "I couldn't find that in the document."
- Be concise and clear
- Quote relevant parts of the document when helpful

Document:
{document}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )

    assistant_message = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_message})
    conversation_store[session_id] = messages

    return jsonify({"response": assistant_message})

@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.get("session_id")
    if session_id:
        document_store.pop(session_id, None)
        conversation_store.pop(session_id, None)
    session.clear()
    return jsonify({"success": True})



if __name__ == "__main__":
    app.run(debug=True)


