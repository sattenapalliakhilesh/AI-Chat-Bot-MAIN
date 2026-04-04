import os
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"
client = Anthropic()

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
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

    session["document"] = text[:20000]
    session["messages"] = []
    return jsonify({"success": True, "preview": text[:200] + "..."})

@app.route("/chat", methods=["POST"])
def chat():
    if "document" not in session:
        return jsonify({"error": "Please upload a document first."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Please type a message."})

    document = session["document"]
    messages = session.get("messages", [])

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
    session["messages"] = messages

    return jsonify({"response": assistant_message})

@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)