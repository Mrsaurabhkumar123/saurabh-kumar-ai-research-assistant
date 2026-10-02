from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./db/faiss_index")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


def get_llm_model() -> str:
    """Return a supported default model when the env is unset or legacy invalid."""
    configured = (os.getenv("LLM_MODEL") or "").strip()
    if not configured or configured == "gpt-4":
        return "gpt-4o-mini"
    return configured


def get_llm_model_candidates() -> list[str]:
    primary = get_llm_model()
    candidates = [primary]
    if primary != "gpt-4o-mini":
        candidates.append("gpt-4o-mini")
    return list(dict.fromkeys(candidates))
