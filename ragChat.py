from vectorDocumentStore import VectorDocumentStore
from app import logger

class RAGChat:
    def __init__(self, client, doc_store: VectorDocumentStore):
        self.client = client
        self.doc_store = doc_store
        
    def chat(self, role: str, query: str, history=None) -> str:
        """Generate a response using RAG"""
        if history is None:
            history = []
        
        docs = self.doc_store.search_documents(role, query, top_k=3)
        if not docs:
            return "I couldn't find any relevant documents to help answer your question."
        
        context = "\n\n".join([
            f"Document: {doc['title']}\n{doc['content']}"
            for doc in docs
        ])
        messages = [
            {"role": "system", "content": f"""You are a helpful assistant with access to {role} documents. 
             Answer the user's question based on the retrieved documents. 
             If the documents don't contain the information needed, acknowledge that.
             Use a professional, helpful tone appropriate for a {role} professional."""},
            {"role": "user", "content": f"Retrieved documents:\n{context}\n\nQuestion: {query}"}
        ]
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while generating a response: {str(e)}"
