def retrieve_context(query, vectorstore, k=3):
    """
    Retrieve relevant context chunks for a given query.
    """
    if vectorstore is None:
        return ""
        
    docs = vectorstore.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context
