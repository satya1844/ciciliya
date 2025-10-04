import chromadb
from chromadb.utils import embedding_functions
from langchain.docstore.document import Document
from typing import List

class ChromaDBManager:
    def __init__(self, path: str = "chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="browsing_chatbot",
            embedding_function=self.sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, docs: List[Document]):
        if not docs:
            return
        
        # Get the list of existing document IDs
        existing_ids = self.collection.get()['ids']
        
        # Only attempt to delete if the list of IDs is not empty
        if existing_ids:
            self.collection.delete(ids=existing_ids)

        self.collection.add(
            documents=[doc.page_content for doc in docs],
            metadatas=[doc.metadata for doc in docs],
            ids=[f"id_{i}" for i in range(len(docs))]
        )

    def query(self, query_text: str, n_results: int = 5) -> List[Document]:
        """
        Queries the collection and returns a list of Langchain Document objects.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["metadatas", "documents"]
        )

        # Check if results are valid and not empty
        if not results or not results.get('documents'):
            return []

        # Reconstruct Document objects from the query results
        retrieved_docs = []
        for i, doc_content in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            retrieved_docs.append(Document(page_content=doc_content, metadata=metadata))
            
        return retrieved_docs