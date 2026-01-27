from langchain_community.vectorstores import FAISS
import os

INDEX_PATH = "rag_index"

def create_vector_store(chunks, embeddings):
    """
    Create a new vector store from document chunks and save it locally.
    If an index already exists, this will load it and add to it.
    """
    if os.path.exists(INDEX_PATH):
        try:
            vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            vectorstore.add_documents(chunks)
        except:
            # If load fails, start fresh
            vectorstore = FAISS.from_documents(chunks, embeddings)
    else:
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
    vectorstore.save_local(INDEX_PATH)
    return vectorstore

def load_vector_store(embeddings):
    """
    Load the existing vector store.
    """
    if not os.path.exists(INDEX_PATH):
        return None
        
    return FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

def clear_vector_store():
    """
    Delete the vector store index to start fresh.
    """
    import shutil
    if os.path.exists(INDEX_PATH):
        shutil.rmtree(INDEX_PATH)
        return True
    return False
