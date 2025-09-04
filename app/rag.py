import os
import glob
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


client = genai.Client(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = "models/embedding-001"
PERSIST_DIR = "chroma_store"


class GeminiEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts
        )
        return [item.values for item in response.embeddings]

    def embed_query(self, text: str) -> list[float]:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text]
        )
        return response.embeddings[0].values


# ---- Ingestion ----
def ingest_documents(data_path="data/travel_blogs"):
    docs = []
    for file_path in glob.glob(f"{data_path}/*.txt"):
        loader = TextLoader(file_path, encoding="utf-8")
        docs.extend(loader.load())

    embeddings = GeminiEmbeddings()

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,  
        collection_name="travel_collection",
        persist_directory=PERSIST_DIR,
    )

    print(f"Ingested {len(docs)} documents into ChromaDB")


def query_documents(query: str):
    embeddings = GeminiEmbeddings()

    vectordb = Chroma(
        collection_name="travel_collection",
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )

    results = vectordb.similarity_search(query, k=5)
    return [r.page_content for r in results]


if __name__ == "__main__":
    ingest_documents()

    res = query_documents("best trekking spots in Himachal")
    print("Search results:")
    for r in res:
        print("-", r)
