from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os

def load_and_split_document(file_path):
    """
    Load a document (PDF or Text) and split it into chunks.
    """
    documents = []
    
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    elif file_path.lower().endswith('.txt') or file_path.lower().endswith('.md'):
        # For text files, we can just read them and create a generic document-like structure if needed,
        # but LangChain has TextLoader too. Let's stick to the user's manual reading if preferred, 
        # or use TextLoader for consistency. Let's use a simple approach for text files to match the previous robustness.
        # However, to be consistent with PyPDFLoader returning 'Document' objects, we should mimic that.
        from langchain_core.documents import Document
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        documents = [Document(page_content=text, metadata={"source": file_path})]
    else:
        raise ValueError("Unsupported file format. Please upload PDF, TXT, or MD.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    chunks = splitter.split_documents(documents)
    return chunks
