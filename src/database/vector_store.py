"""
ChromaDB Vector Store Manager

Handles document storage for the application.
Uses in-memory storage to avoid model downloads.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config import settings


class SimpleDocumentStore:
    """
    Simple in-memory document store that doesn't require embeddings or model downloads.
    """
    
    def __init__(self):
        """Initialize simple document store."""
        self.collections = {
            "applicant_documents": {},
            "knowledge_base": {}
        }
    
    def get_or_create_collection(self, name: str, metadata: Dict = None):
        """Get or create a collection."""
        if name not in self.collections:
            self.collections[name] = {}
        return self.collections[name]
    
    def get_collection(self, name: str):
        """Get a collection."""
        return self.collections.get(name, {})


class VectorStore:
    """
    Document storage using simple in-memory collections.
    No embeddings or model downloads - completely local.
    
    Collections:
    - applicant_documents: Uploaded documents
    - knowledge_base: Eligibility rules and policies
    """
    
    def __init__(self, persist_dir: str = None):
        """
        Initialize document store.
        
        Args:
            persist_dir: Directory for persistence (not used, in-memory only)
        """
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Use simple in-memory store
        self.client = SimpleDocumentStore()
        
        # Initialize collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Create or get existing collections."""
        # Applicant documents collection
        self.documents_collection = self.client.get_or_create_collection(
            name="applicant_documents",
            metadata={"description": "Applicant uploaded documents"}
        )
        
        # Knowledge base collection
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Eligibility rules and policies"}
        )
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any],
        collection_name: str = "applicant_documents"
    ) -> str:
        """
        Add document to collection.
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Document metadata
            collection_name: Target collection
            
        Returns:
            Document ID
        """
        collection = self.client.get_collection(collection_name)
        collection[doc_id] = {
            'document': text,
            'metadata': metadata,
            'id': doc_id
        }
        return doc_id
    
    def add_documents_batch(
        self,
        doc_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "applicant_documents"
    ):
        """
        Add multiple documents in batch.
        
        Args:
            doc_ids: List of document identifiers
            texts: List of document texts
            metadatas: List of metadata dictionaries
            collection_name: Target collection
        """
        collection = self.client.get_collection(collection_name)
        for doc_id, text, metadata in zip(doc_ids, texts, metadatas):
            collection[doc_id] = {
                'document': text,
                'metadata': metadata,
                'id': doc_id
            }
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        collection_name: str = "applicant_documents"
    ) -> Dict[str, Any]:
        """
        Retrieve documents (no semantic search needed).
        
        Args:
            query: Search query text (not used)
            n_results: Number of results to return
            where: Metadata filters (not used)
            collection_name: Collection to search
            
        Returns:
            Documents from collection
        """
        collection = self.client.get_collection(collection_name)
        
        # Return all documents up to n_results
        docs = list(collection.values())[:n_results]
        return {
            'documents': [d['document'] for d in docs],
            'metadatas': [d['metadata'] for d in docs],
            'ids': [d['id'] for d in docs]
        }
    
    def get_document(
        self,
        doc_id: str,
        collection_name: str = "applicant_documents"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific document by ID.
        
        Args:
            doc_id: Document identifier
            collection_name: Collection to search
            
        Returns:
            Document data or None
        """
        collection = self.client.get_collection(collection_name)
        
        if doc_id in collection:
            doc = collection[doc_id]
            return {
                'id': doc['id'],
                'document': doc['document'],
                'metadata': doc['metadata']
            }
        return None
    
    def delete_document(
        self,
        doc_id: str,
        collection_name: str = "applicant_documents"
    ):
        """Delete document from collection."""
        collection = self.client.get_collection(collection_name)
        if doc_id in collection:
            del collection[doc_id]
    
    def initialize_knowledge_base(self):
        """
        Initialize knowledge base with eligibility rules and policies.
        """
        knowledge_items = [
            {
                "id": "rule_income",
                "text": "Applicants with monthly income below AED 15,000 are eligible for social support. Income is calculated from bank statements and employment verification.",
                "metadata": {"type": "eligibility_rule", "category": "income"}
            },
            {
                "id": "rule_family",
                "text": "Larger family sizes (3 or more members) receive additional consideration. Family size affects the support amount and priority.",
                "metadata": {"type": "eligibility_rule", "category": "family"}
            },
            {
                "id": "rule_employment",
                "text": "Unemployed applicants receive higher priority for support. Employment status is verified through resume and employment history.",
                "metadata": {"type": "eligibility_rule", "category": "employment"}
            },
            {
                "id": "rule_assets",
                "text": "Asset-to-liability ratio below 0.5 indicates financial need. This is calculated from the assets and liabilities Excel sheet.",
                "metadata": {"type": "eligibility_rule", "category": "wealth"}
            },
            {
                "id": "rule_credit",
                "text": "Credit scores are considered but not disqualifying. Minimum credit score of 300 required. Poor credit may indicate financial hardship.",
                "metadata": {"type": "eligibility_rule", "category": "credit"}
            },
            {
                "id": "enablement_upskilling",
                "text": "Economic enablement through upskilling includes: Digital Skills Training, Financial Literacy Course, Vocational Training Program, and Language Enhancement Course.",
                "metadata": {"type": "enablement_program", "category": "upskilling"}
            },
            {
                "id": "enablement_jobs",
                "text": "Job matching services include: Government Job Portal Registration, Private Sector Job Fair access, and Freelance Opportunities Platform.",
                "metadata": {"type": "enablement_program", "category": "job_matching"}
            },
            {
                "id": "enablement_counseling",
                "text": "Career counseling services include: One-on-One Career Guidance, Resume Building Workshop, and Interview Preparation Session.",
                "metadata": {"type": "enablement_program", "category": "counseling"}
            }
        ]
        
        for item in knowledge_items:
            self.add_document(
                doc_id=item["id"],
                text=item["text"],
                metadata=item["metadata"],
                collection_name="knowledge_base"
            )
    
    def query_knowledge_base(self, query: str, n_results: int = 3) -> List[str]:
        """
        Query knowledge base for relevant rules and policies.
        
        Args:
            query: Query text (not used)
            n_results: Number of results
            
        Returns:
            List of relevant knowledge items
        """
        results = self.search(
            query=query,
            n_results=n_results,
            collection_name="knowledge_base"
        )
        
        if results['documents']:
            return results['documents']
        return []


# Global vector store instance
vector_store = VectorStore()

# Initialize knowledge base on first import (idempotent)
try:
    collection = vector_store.client.get_collection("knowledge_base")
    if len(collection) == 0:
        vector_store.initialize_knowledge_base()
except Exception as e:
    print(f"Warning: Could not initialize knowledge base: {e}")
