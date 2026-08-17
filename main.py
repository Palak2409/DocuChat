import os
import uuid
import shutil
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from docx import Document
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings


UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


chroma_client = Client(Settings())


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embedding_model()



def get_gemini_model():
    """Configures and returns the Gemini Pro model."""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY not found in Streamlit secrets.")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.error(f"Error configuring Gemini: {e}")
        return None

def extract_text_from_pdf(file_path):
    """Extracts text from PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

def extract_text_from_docx(file_path):
    """Extracts text from DOCX."""
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def chunk_text(text, max_chars=1000, overlap=200):
    """Splits text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start += max_chars - overlap
    return chunks

def create_vector_db(uploaded_files):
    """
    Processes files, creates a temporary Chroma collection, 
    and returns the collection name and a combined text preview for summarization.
    """
    
    collection_name = f"session_{uuid.uuid4().hex}"
    collection = chroma_client.create_collection(name=collection_name)
    
    full_text_preview = "" 

    for uploaded_file in uploaded_files:
        # Save to temp file
        temp_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(temp_path)
        elif ext in [".doc", ".docx"]:
            text = extract_text_from_docx(temp_path)
        else:
            continue 
        
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        
        if len(full_text_preview) < 10000:
            full_text_preview += f"\n\n--- Document: {uploaded_file.name} ---\n"
            full_text_preview += text[:2000] 

        
        chunks = chunk_text(text)
        if chunks:
            embeddings = embed_model.encode(chunks).tolist()
            
            metadatas = [{"source": uploaded_file.name} for _ in chunks]
            ids = [f"{uuid.uuid4().hex}" for _ in chunks]
            collection.add(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)

    return collection_name, full_text_preview

def generate_summary(text_preview):
    """Generates a brief summary of the uploaded content."""
    model = get_gemini_model()
    if not model: return "Error loading model."
    
    prompt = (
        "You are a research assistant. The user has uploaded the following documents. "
        "Provide a concise, bullet-point summary of the main topics covered in these document snippets.\n\n"
        f"Documents Preview:\n{text_preview}"
    )
    response = model.generate_content(prompt)
    return response.text

def query_llm(collection_name, query):
    """Retrieves context and answers the question."""
    model = get_gemini_model()
    if not model: return "Error loading model."

    try:
        collection = chroma_client.get_collection(name=collection_name)
        results = collection.query(query_texts=[query], n_results=5)
        
        if not results["documents"][0]:
            return "I couldn't find relevant information in the documents."

        context = "\n\n".join(results["documents"][0])
        
        # RAG Prompt
        prompt = (
            "You are a helpful AI assistant. Answer the user's question based *only* on the provided context. "
            "Synthesize the answer in your own words. Do not copy sentences verbatim.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error processing request: {e}"

# Main Application

def main():
    st.set_page_config(page_title="DocuChat AI", layout="wide")
    
    st.title("📄 DocuChat: Multi-Doc AI Assistant")
    st.write("Upload multiple documents, get a summary, and chat with them instantly.")

    #  Sidebar: File Upload
    with st.sidebar:
        st.header("Upload Documents")
        uploaded_files = st.file_uploader(
            "Select PDF or DOCX files", 
            type=["pdf", "doc", "docx"], 
            accept_multiple_files=True
        )
        
        process_btn = st.button("Process & Summarize")

   
    if "collection_name" not in st.session_state:
        st.session_state.collection_name = None
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    #  Processing Logic 
    if process_btn and uploaded_files:
        with st.spinner("Processing documents and generating summary..."):
            # 1. Clear old data if exists
            if st.session_state.collection_name:
                try:
                    chroma_client.delete_collection(st.session_state.collection_name)
                except: pass
            
            st.session_state.messages = [] # Reset chat
            
            # 2. Create new DB
            col_name, text_preview = create_vector_db(uploaded_files)
            st.session_state.collection_name = col_name
            
            # 3. Generate Summary
            summary = generate_summary(text_preview)
            st.session_state.summary = summary
            
            # 4. Add summary to chat history
            st.session_state.messages.append({"role": "assistant", "content": f"**Document Summary:**\n\n{summary}"})

    #  Streamlit Interface 
    
    # If no documents processed yet
    if not st.session_state.collection_name:
        st.info("👈 Please upload documents and click 'Process & Summarize' to start.")
    else:
        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        if prompt := st.chat_input("Ask a question about your documents..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate Answer
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = query_llm(st.session_state.collection_name, prompt)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()