import chromadb
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        self.model = None
        self.enabled = False
        
    def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            
            os.makedirs("./chroma_db", exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path="./chroma_db")
            
            
            self.collection = self.client.get_or_create_collection(
                name="chapters",
                metadata={"description": "Book chapters with semantic search"}
            )
            
     
            logger.info("Loading SentenceTransformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.enabled = True
            logger.info("ChromaDB initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            self.enabled = False
            return False
    
    def add_chapter(self, content, metadata):
        """Add a chapter to the vector store"""
        if not self.enabled:
            logger.warning("ChromaDB not enabled, skipping add_chapter")
            return False
        
        try:
            
            timestamp = metadata.get('timestamp', datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            version_id = metadata.get('version_id', 'unknown')
            doc_id = f"chapter_{timestamp}_{version_id}"
            
            
            try:
                existing = self.collection.get(ids=[doc_id])
                if existing['ids']:
                    logger.info(f"Document {doc_id} already exists, updating...")
                    self.collection.update(
                        ids=[doc_id],
                        documents=[content],
                        metadatas=[metadata]
                    )
                    return True
            except Exception:
                pass  
            
            # Add new document
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Successfully added chapter: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to ChromaDB: {e}")
            return False
    
    def search_chapters(self, query, n_results=5):
        """Search chapters using semantic similarity"""
        if not self.enabled:
            logger.warning("ChromaDB not enabled, returning empty results")
            return []
        
        try:
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, 100)  
            )
            
            search_results = []
            
            # Process results
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Create preview (first 200 characters)
                    preview = doc[:200] + "..." if len(doc) > 200 else doc
                    
                    search_results.append({
                        'content': preview,
                        'full_content': doc,  
                        'metadata': metadata,
                        'distance': distance,
                        'similarity_score': 1 - distance  
                    })
            
            # Sort by similarity 
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Found {len(search_results)} results for query: '{query}'")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    def get_all_chapters(self):
        """Get all stored chapters"""
        if not self.enabled:
            return []
        
        try:
            # Get all documents
            results = self.collection.get()
            
            all_chapters = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    doc_id = results['ids'][i] if results['ids'] else f"doc_{i}"
                    
                    all_chapters.append({
                        'id': doc_id,
                        'content': doc[:200] + "..." if len(doc) > 200 else doc,
                        'full_content': doc,
                        'metadata': metadata
                    })
            
            return all_chapters
            
        except Exception as e:
            logger.error(f"Error getting all chapters: {e}")
            return []
    
    def delete_chapter(self, doc_id):
        """Delete a chapter by ID"""
        if not self.enabled:
            return False
        
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted chapter: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chapter {doc_id}: {e}")
            return False
    
    def get_collection_stats(self):
        """Get statistics about the collection"""
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            count = self.collection.count()
            return {
                "status": "enabled",
                "total_chapters": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"status": "error", "error": str(e)}

# Global instance
vector_store = VectorStore()