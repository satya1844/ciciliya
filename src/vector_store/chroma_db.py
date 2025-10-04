import chromadb
from chromadb.utils import embedding_functions
from typing import List,Optional
from langchain.docstore.document import Document
import uuid

class ChromaDBManager:
  def __init__ (self, db_path:Optional[str] = None, collection_name: str = "ciciliya_store"):
    self.collection_name = f"{collection_name}-{uuid.uuid4()}"
    self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    if db_path:
      self.client = chromadb.PersistentClient(path=db_path)
    else:
      self.client = chromadb.Client()

    self.collection = self.client.get_or_create_collection(name=self.collection_name, embedding_function=self.embedding_function)

  def add_documents(self, documents: List[Document]):
    if not documents:
      return
    
    self.collection.add(
      documents=[doc.page_content for doc in documents],
      metadatas=[doc.metadata for doc in documents],
      ids=[str(uuid.uuid4()) for i in range(len(documents))]
    )


  def query(self, query_text: str, n_results: int = 3) -> List[Document]:
    if self.collection.count() == 0:
      return []
    
    results = self.collection.query(
      query_texts=[query_text],
      n_results=n_results
    )

    if results and results['documents']:
      return results['documents'][0]
    else:
      return []


  def get_collection_count(self) -> int:
    return self.collection.count()


  def reset(self):
    self.client.delete_collection(name=self.collection_name)
    self.collection = self.client.get_or_create_collection(name=self.collection_name, embedding_function=self.embedding_function)