"""
RAG (Retrieval-Augmented Generation) System for Travel Information
Uses FAISS vector store and OpenAI embeddings for semantic search
"""

import json
import os
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class TravelRAG:
    def __init__(self, data_path: str = "data/travel_data.json"):
        """Initialize RAG system with travel data"""
        self.data_path = data_path
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.travel_data = None
        
        # Load and index travel data
        self._load_data()
        self._create_vector_store()
    
    def _load_data(self):
        """Load travel data from JSON"""
        try:
            with open(self.data_path, 'r') as f:
                self.travel_data = json.load(f)
            print(f"✅ Loaded travel data from {self.data_path}")
        except Exception as e:
            print(f"❌ Error loading travel data: {e}")
            self.travel_data = {"routes": [], "travel_tips": [], "popular_destinations": []}
    
    def _create_vector_store(self):
        """Create FAISS vector store from travel data"""
        documents = []
        
        # Add routes as documents
        for route in self.travel_data.get("routes", []):
            content = f"""
Route: {route['origin']} to {route['destination']}
Distance: {route['distance_km']} km
Available modes: {', '.join(route['modes'])}
{f"Flight time: {route.get('avg_flight_time', 'N/A')}" if 'flight' in route['modes'] else ''}
{f"Train time: {route.get('avg_train_time', 'N/A')}" if 'train' in route['modes'] else ''}
{f"Bus time: {route.get('avg_bus_time', 'N/A')}" if 'bus' in route['modes'] else ''}
Popular times: {', '.join(route['popular_times'])}
Tips: {route['tips']}
"""
            metadata = {
                "type": "route",
                "origin": route['origin'],
                "destination": route['destination'],
                "modes": route['modes']
            }
            documents.append(Document(page_content=content.strip(), metadata=metadata))
        
        # Add travel tips as documents
        for tip in self.travel_data.get("travel_tips", []):
            documents.append(Document(
                page_content=f"Travel Tip: {tip}",
                metadata={"type": "tip"}
            ))
        
        # Add destination information
        for dest in self.travel_data.get("popular_destinations", []):
            content = f"""
Destination: {dest['city']}
Best time to visit: {dest['best_time']}
Attractions: {', '.join(dest['attractions'])}
Popular routes from: {', '.join(dest['travel_from'])}
"""
            documents.append(Document(
                page_content=content.strip(),
                metadata={"type": "destination", "city": dest['city']}
            ))
        
        # Create vector store
        try:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            print(f"✅ Created vector store with {len(documents)} documents")
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
    
    def retrieve_travel_info(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve relevant travel information using semantic search
        
        Args:
            query: User's travel query
            k: Number of results to return
            
        Returns:
            List of relevant documents with content and metadata
        """
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        except Exception as e:
            print(f"❌ Error retrieving info: {e}")
            return []
    
    def get_route_info(self, origin: str, destination: str) -> Dict:
        """Get specific route information"""
        for route in self.travel_data.get("routes", []):
            if (route['origin'].lower() == origin.lower() and 
                route['destination'].lower() == destination.lower()):
                return route
        return None
    
    def get_route_suggestions(self, origin: str, destination: str) -> str:
        """Get AI-enhanced route suggestions using RAG"""
        query = f"Travel from {origin} to {destination}"
        results = self.retrieve_travel_info(query, k=2)
        
        if not results:
            return f"I don't have specific information about traveling from {origin} to {destination}."
        
        # Combine retrieved information
        info_parts = []
        for result in results:
            if result['metadata'].get('type') == 'route':
                info_parts.append(result['content'])
        
        return "\n\n".join(info_parts) if info_parts else "No route information found."
    
    def get_travel_tips(self, location: str = None) -> List[str]:
        """Get general or location-specific travel tips"""
        if location:
            query = f"Travel tips for {location}"
            results = self.retrieve_travel_info(query, k=3)
            return [r['content'] for r in results if 'tip' in r['content'].lower()]
        else:
            return self.travel_data.get("travel_tips", [])[:5]

# Singleton instance
_travel_rag_instance = None

def get_travel_rag() -> TravelRAG:
    """Get or create TravelRAG singleton instance"""
    global _travel_rag_instance
    if _travel_rag_instance is None:
        _travel_rag_instance = TravelRAG()
    return _travel_rag_instance
