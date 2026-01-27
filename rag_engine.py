from rag_loader import load_and_split_document
from rag_embeddings import embedding_model
from rag_vectorstore import create_vector_store, load_vector_store, clear_vector_store
from rag_retriever import retrieve_context

class RAGEngine:
    def __init__(self):
        """
        Initialize the RAG engine by loading the vector store.
        """
        self.vector_store = load_vector_store(embedding_model)

    def process_file(self, file_path: str, filename: str) -> tuple[bool, str]:
        """
        Process a file and update the vector store.
        """
        try:
            chunks = load_and_split_document(file_path)
            self.vector_store = create_vector_store(chunks, embedding_model)
            return True, f"Successfully processed {filename}. Added {len(chunks)} chunks to knowledge base."
        except Exception as e:
            return False, f"Error processing file: {str(e)}"

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """
        Retrieve relevant context for a query.
        """
        # We need to access the internal 'similarity_search' of vectorstore or just use the helper 
        # But 'retrieve_context' helper returns a string, so we might want to expose raw docs if needed 
        # or just reuse the helper for the text.
        # The original 'retrieve' returned a list of strings.
        
        if self.vector_store is None:
            return []
            
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def get_formatted_context(self, query: str) -> str:
        """
        Get context formatted as a string for the LLM prompt.
        """
        context = retrieve_context(query, self.vector_store)
        if not context:
            return ""
        
        return f"CONTEXT FROM UPLOADED DOCUMENTS:\n{context}\n---\n"

    def clear_knowledge_base(self) -> bool:
        """
        Clear all documents from the knowledge base.
        """
        result = clear_vector_store()
        self.vector_store = None
        return result
