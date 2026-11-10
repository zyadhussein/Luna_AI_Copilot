from openai import OpenAI
from rag.documents import POLICY_DOCUMENTS


embedding_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

EMBEDDING_MODEL = "nomic-embed-text-v1.5"

def embed_document(text: str) -> list[float]:
    response = embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=f"search_document: {text}"
    )

    return response.data[0].embedding
def embed_query(text: str) -> list[float]:
    response = embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=f"search_query: {text}"
    )

    return response.data[0].embedding

import math


def cosine_similarity(
    a: list[float],
    b: list[float]
) -> float:

    dot_product = sum(
        x * y for x, y in zip(a, b)
    )

    magnitude_a = math.sqrt(
        sum(x * x for x in a)
    )

    magnitude_b = math.sqrt(
        sum(y * y for y in b)
    )

    return dot_product / (
        magnitude_a * magnitude_b
    )
def build_document_index():
    indexed_documents = []

    for document in POLICY_DOCUMENTS:

        embedding = embed_document(
            document["text"]
        )

        indexed_documents.append({
            **document,
            "embedding": embedding
        })

    return indexed_documents

def retrieve(
    query: str,
    indexed_documents: list,
    top_k: int = 2
):
    query_embedding = embed_query(query)

    results = []

    for document in indexed_documents:

        score = cosine_similarity(
            query_embedding,
            document["embedding"]
        )

        results.append({
            "id": document["id"],
            "title": document["title"],
            "text": document["text"],
            "score": score
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]
INDEXED_DOCUMENTS = build_document_index()


def retrieve_policy(
    query: str,
    top_k: int = 2
):
    return retrieve(
        query,
        INDEXED_DOCUMENTS,
        top_k
    )
if __name__ == "__main__":

    index = build_document_index()

    results = retrieve(
        "Can I bring my dog?",
        index
    )

    for result in results:
        print(
            result["title"],
            result["score"]
        )
