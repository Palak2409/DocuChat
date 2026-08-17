# 📄 DocuChat: Multi-Document AI Assistant

**DocuChat** is a streamlined, AI-powered research tool that allows users to upload multiple PDF and DOCX documents and interact with them using natural language. Built with Streamlit and Google Gemini, it uses Retrieval-Augmented Generation (RAG) to provide accurate, context-aware answers and summaries.

---

## 🚀 Features

- Multi-Document Support: Upload and analyze multiple PDF and DOCX files simultaneously.
- Instant Summarization: Automatically generates a concise summary of all uploaded content upon processing.
- Context-Aware Chat: Ask questions and get answers based strictly on the provided documents.
- Privacy-Focused: All data is processed in a temporary session and cleared when the page is refreshed. No permanent storage.
- Fast & Efficient: Uses PyMuPDF for rapid text extraction and ChromaDB for high-speed vector search.

---

## 🛠️ Tech Stack

**Frontend: Streamlit**

- **LLM**: Google Gemini 2.5 Flash (via google-generativeai)
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Text Extraction**: PyMuPDF (PDFs) and python-docx (Word docs)

---

## ⚙️ Installation & Setup

Follow these steps to run the application locally.

### 1. Clone the Repository
```bash
git clone https://github.com/Ishita-01/DocuChat.git
```

### 2. Create a Virtual Environment (Recommended)

It's best practice to use a virtual environment to manage dependencies.

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key

- You need a Google Gemini API key to run the model.
- Get your key from Google AI Studio.
- Create a folder named .streamlit in the root directory.
- Inside that folder, create a file named secrets.toml.
- Add your key to the file:
4. Add your key to the file:

```toml
# `.streamlit/secrets.toml`
GEMINI_API_KEY = "your_actual_api_key_here"
```
---

## ▶️ Usage

### Start the application:
```bash
streamlit run app.py
```

- The app will open in your default browser (usually at http://localhost:8501).
- Sidebar: Use the "Upload Documents" button to select one or more PDF/DOCX files.
- Click "Process & Summarize".
- Wait for the summary to appear in the chat.
- Type your questions in the chat input box to query your documents.

---

## 🧠 How It Works

- **Ingestion**: The app extracts text from uploaded files.
- **Chunking**: Text is split into smaller, overlapping chunks to preserve context.
- **Embedding**: The all-MiniLM-L6-v2 model converts these chunks into vector embeddings.
- **Storage**: Embeddings are stored in a temporary, in-memory ChromaDB collection.
- **Retrieval**: When you ask a question, the system searches for the most relevant text chunks.
- **Generation**: The relevant chunks + your question are sent to Gemini 2.5 Flash, which generates an answer based solely on that context.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.




