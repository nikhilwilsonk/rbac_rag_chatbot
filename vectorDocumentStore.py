from datetime import time
from pathlib import Path
from typing import List
import chromadb
from config import DOCUMENTS_DIR, ROLES, VECTOR_DB_PATH,get_openai_api_key
from chromadb.utils import embedding_functions
from app import logger

class VectorDocumentStore:
    def __init__(self, client, db_path: Path = VECTOR_DB_PATH, docs_dir: Path = DOCUMENTS_DIR):
        self.client = client
        self.db_path = db_path
        self.docs_dir = docs_dir
        
        self.chroma_client = chromadb.PersistentClient(path=str(db_path))
        
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=get_openai_api_key(),
            model_name="text-embedding-ada-002"
        )
        
        self.collections = {}
        for role in ROLES:
            try:
                self.collections[role] = self.chroma_client.get_collection(
                    name=f"{role}_docs",
                    embedding_function=self.embedding_function
                )
            except chromadb.errors.InvalidCollectionException:
                self.collections[role] = self.chroma_client.create_collection(
                    name=f"{role}_docs",
                    embedding_function=self.embedding_function
                )
            
            role_dir = self.docs_dir / role
            role_dir.mkdir(exist_ok=True)
    
    def add_document(self, role: str, title: str, content: str) -> bool:
        """Add a document for a specific role and store in vector database"""
        if role not in ROLES:
            logger.warning(f"Invalid role: {role}")
            return False
        
        doc_path = self.docs_dir / role / f"{title.replace(' ', '_')}.txt"
        with open(doc_path, 'w') as f:
            f.write(content)
        
        try:
            doc_id = f"{role}_{title.replace(' ', '_')}_{int(time.time())}"
            existing_docs = self.collections[role].get(
                where={"title": title}
            )
            if existing_docs and len(existing_docs['ids']) > 0:
                self.collections[role].delete(
                    ids=existing_docs['ids']
                )
                logger.info(f"Replaced existing document '{title}' for role '{role}'")
            self.collections[role].add(
                documents=[content],
                metadatas=[{"title": title, "path": str(doc_path)}],
                ids=[doc_id]
            )
            logger.info(f"Added document '{title}' for role '{role}'")
            return True
        
        except Exception as e:
            logger.error(f"Error adding document to vector database: {str(e)}")
            return False
    
    def list_documents(self, role: str) -> List[str]:
        """List all documents available for a specific role"""
        if role not in ROLES:
            logger.warning(f"Invalid role: {role}")
            return []
        
        try:
            result = self.collections[role].get()
            if not result or 'metadatas' not in result or len(result['metadatas']) == 0:
                return []
            
            return [meta.get('title', 'Untitled') for meta in result['metadatas']]
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def search_documents(self, role: str, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant documents based on query embedding"""
        if role not in ROLES:
            logger.warning(f"Invalid role: {role}")
            return []
        
        try:
            results = self.collections[role].query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or 'documents' not in results or len(results['documents']) == 0:
                return []
            
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                title = results['metadatas'][0][i].get('title', 'Untitled')
                score = results['distances'][0][i] if 'distances' in results else 0.0
                similarity = 1.0 - min(score, 1.0)  
                formatted_results.append({
                    "title": title,
                    "content": doc,
                    "score": similarity
                })
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

