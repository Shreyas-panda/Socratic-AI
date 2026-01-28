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
            # Track document metadata
            self.add_document_metadata(filename, len(chunks))
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
        Includes anti-hallucination instructions.
        """
        context = retrieve_context(query, self.vector_store)
        if not context:
            return ""
        
        # Anti-hallucination guardrails
        return f"""CONTEXT FROM USER'S UPLOADED DOCUMENTS:
---
{context}
---
IMPORTANT: When answering, you MUST:
1. Base your response on the context above when relevant
2. If information is not in the context, say "Based on my knowledge..." before answering
3. Never fabricate specific facts, quotes, or statistics not in the context
4. If asked about something not covered, honestly say it's not in the uploaded documents
"""

    def get_formatted_context_for_files(self, query: str, filenames: list) -> str:
        """
        Get context formatted as a string, filtered to specific files.
        When files are tagged, we retrieve ALL chunks from those files first,
        then use similarity to rank them.
        
        Args:
            query: The user's question
            filenames: List of filenames to filter results to
        """
        if self.vector_store is None:
            return ""
        
        # First, get ALL documents from the specified files
        all_matching_docs = []
        try:
            for doc_id, doc in self.vector_store.docstore._dict.items():
                doc_source = doc.metadata.get('source', '')
                for filename in filenames:
                    # Match filename at the end of the path or as substring
                    if filename in doc_source or doc_source.endswith(filename):
                        all_matching_docs.append(doc)
                        break
        except Exception as e:
            print(f"Error accessing docstore: {e}")
            # Fallback: try similarity search with a generic query
            all_matching_docs = []
        
        if not all_matching_docs:
            return f"(No content found from the specified files: {', '.join(filenames)}. Please ensure the files are uploaded to the knowledge base.)"
        
        # If we have matching docs, use similarity search within them
        # to find the most relevant chunks for the query
        if len(all_matching_docs) <= 3:
            # If we have 3 or fewer chunks, use them all
            filtered_docs = all_matching_docs
        else:
            # Use the embedding model to find most relevant chunks
            try:
                from rag_embeddings import embedding_model
                import numpy as np
                
                # Get query embedding
                query_embedding = embedding_model.embed_query(query)
                
                # Get embeddings for all matching docs and calculate similarity
                doc_similarities = []
                for doc in all_matching_docs:
                    doc_embedding = embedding_model.embed_query(doc.page_content)
                    # Cosine similarity
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    doc_similarities.append((doc, similarity))
                
                # Sort by similarity and take top 5
                doc_similarities.sort(key=lambda x: x[1], reverse=True)
                filtered_docs = [doc for doc, _ in doc_similarities[:5]]
            except Exception as e:
                print(f"Error during similarity ranking: {e}")
                # Fallback: just take first 5 docs
                filtered_docs = all_matching_docs[:5]
        
        context = "\n\n".join([doc.page_content for doc in filtered_docs])
        
        # Anti-hallucination guardrails
        return f"""CONTEXT FROM REFERENCED DOCUMENTS ({', '.join(filenames)}):
---
{context}
---
IMPORTANT: When answering, you MUST:
1. Base your response PRIMARILY on the context from the referenced files above
2. If information is not in the referenced files, say "This isn't covered in the referenced documents, but based on my knowledge..." before answering
3. Never fabricate specific facts, quotes, or statistics
4. Cite which document the information comes from when possible
"""

    def clear_knowledge_base(self) -> bool:
        """
        Clear all documents from the knowledge base.
        """
        result = clear_vector_store()
        self.vector_store = None
        # Also clear the document metadata
        self._clear_document_metadata()
        return result
    
    def get_knowledge_base_info(self) -> dict:
        """
        Get information about all documents in the knowledge base.
        Returns list of documents with their metadata.
        """
        import os
        import json
        
        metadata_file = "rag_index/documents_metadata.json"
        documents = []
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    documents = json.load(f)
            except:
                pass
        
        # Get total chunks from vector store
        total_chunks = 0
        if self.vector_store:
            try:
                total_chunks = len(self.vector_store.docstore._dict)
            except:
                pass
        
        return {
            "documents": documents,
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "has_content": self.vector_store is not None and total_chunks > 0
        }
    
    def add_document_metadata(self, filename: str, chunks_count: int):
        """
        Store metadata about uploaded documents.
        """
        import os
        import json
        from datetime import datetime
        
        metadata_dir = "rag_index"
        metadata_file = os.path.join(metadata_dir, "documents_metadata.json")
        
        # Ensure directory exists
        os.makedirs(metadata_dir, exist_ok=True)
        
        # Load existing metadata
        documents = []
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    documents = json.load(f)
            except:
                pass
        
        # Add new document
        documents.append({
            "filename": filename,
            "chunks": chunks_count,
            "uploaded_at": datetime.now().isoformat()
        })
        
        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(documents, f, indent=2)
    
    def _clear_document_metadata(self):
        """Clear the document metadata file."""
        import os
        metadata_file = "rag_index/documents_metadata.json"
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
