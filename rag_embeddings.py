from langchain_huggingface import HuggingFaceEmbeddings

# Initialize the embedding model
# using clean, lightweight local model as requested
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
