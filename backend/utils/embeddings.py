import os
from sentence_transformers import SentenceTransformer
from config import get_llm_model
from utils.logger import api_logger

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


def get_embedding(text: str):
    """
    Get embedding vector for text using a local SentenceTransformer model.
    Returns a Python list compatible with the existing FAISS code.
    """
    api_logger.debug(f"🔢 Generating local embedding - Model: {MODEL_NAME}, Text length: {len(text)} chars")
    embedding = model.encode(text, normalize_embeddings=True)
    api_logger.debug(f"✅ Local embedding generated | Dimension: {len(embedding)}")
    return embedding.tolist()


def call_openai(prompt: str, model: str = None):
    """
    Generic OpenAI API call wrapper for agents
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if model is None:
        model = get_llm_model()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
