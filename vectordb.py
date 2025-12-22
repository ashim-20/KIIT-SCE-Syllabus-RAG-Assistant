import os
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VectorDB:
    """
    A simple vector database wrapper using ChromaDB with HuggingFace embeddings.
    """

    def __init__(self, collection_name: str = None, embedding_model: str = None):
        """
        Initialize the vector database.
        """
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION_NAME", "rag_documents"
        )
        self.embedding_model_name = embedding_model or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize ChromaDB client (Persistent - saves to disk)
        self.client = chromadb.PersistentClient(path="./chroma_db")

        # Load embedding model
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "RAG document collection"},
        )

        print(f"Vector database initialized with collection: {self.collection_name}")

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Splits text using RecursiveCharacterTextSplitter to respect document structure.
        """
        # OPTION 2: Use LangChain's RecursiveCharacterTextSplitter
        # Customized separators for Syllabus structure
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            separators=["\nUNIT ", "\nCourse Title", "\n\n", "\n", " ", ""]
        )
        
        # Split text into Document objects then extract content
        docs = text_splitter.create_documents([text])
        chunks = [doc.page_content for doc in docs]

        return chunks

    def add_documents(self, documents: List[dict]) -> None:
        """
        Add documents to the vector database.
        """
        print(f"Processing {len(documents)} documents...")
        
        all_ids = []
        all_documents = []
        all_metadatas = []
        all_embeddings = []

        for doc_idx, doc in enumerate(documents):
            content = doc.get("content", "")
            base_metadata = doc.get("metadata", {})

            # Split document into chunks
            chunks = self.chunk_text(content)

            # Prepare batch data
            for chunk_idx, chunk_text in enumerate(chunks):
                # Create unique ID
                chunk_id = f"doc_{doc_idx}_chunk_{chunk_idx}"
                
                # Metadata (must be simple key-values for Chroma)
                meta = {k: str(v) for k, v in base_metadata.items()}
                
                all_ids.append(chunk_id)
                all_documents.append(chunk_text)
                all_metadatas.append(meta)

        if not all_documents:
            print("No content to add.")
            return

        # Check if data already exists to avoid re-embedding
        existing_count = self.collection.count()
        if existing_count > 0:
            print(f"[INFO] Collection already contains {existing_count} chunks. Skipping re-embedding.")
            return

        print(f"Creating embeddings for {len(all_documents)} chunks... (This may take time)")
        
        # Create embeddings in batches to avoid memory issues
        batch_size = 64
        total_chunks = len(all_documents)
        
        for i in range(0, total_chunks, batch_size):
            end = min(i + batch_size, total_chunks)
            batch_docs = all_documents[i:end]
            batch_ids = all_ids[i:end]
            batch_metas = all_metadatas[i:end]
            
            # Encode batch
            batch_embeddings = self.embedding_model.encode(batch_docs).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_metas
            )
            print(f"Indexed {end}/{total_chunks} chunks...", end="\r")

        print("\nDocuments added to vector database")

    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for similar documents in the vector database.
        """
        # Create query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()

        # Query the collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        # Handle empty results
        if not results['ids']:
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}

        # Flatten results (Chroma returns list of lists)
        return {
            "documents": results['documents'][0],
            "metadatas": results['metadatas'][0],
            "distances": results['distances'][0],
            "ids": results['ids'][0],
        }