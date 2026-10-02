"""
Summarizer Agent: Summarizes retrieved chunks into a coherent answer
"""
import os
from openai import OpenAI
from config import get_llm_model, get_llm_model_candidates
from utils.logger import agent_logger


class SummarizerAgent:
    def __init__(self):
        self.name = "Summarizer Agent"
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        agent_logger.info(f"{self.name} initialized")

    def summarize(self, query: str, chunks: list[str], conversation_context: str = ""):
        """
        Summarize retrieved chunks into a coherent answer

        Args:
            query: Original user question
            chunks: List of relevant text chunks from FAISS
            conversation_context: Previous conversation history for follow-up queries

        Returns:
            dict with summary and metadata
        """
        agent_logger.info(f"{self.name}: Starting summarization for query='{query}'")
        agent_logger.debug(f"{self.name}: Processing {len(chunks)} chunks")

        if not chunks:
            agent_logger.warning(f"{self.name}: No chunks provided for summarization")
            return {
                "status": "error",
                "message": "No chunks to summarize",
                "summary": ""
            }

        # Combine chunks into context
        context = "\n\n---\n\n".join(chunks)

        # Add conversation context if available
        conversation_prefix = ""
        if conversation_context:
            conversation_prefix = f"{conversation_context}\n\n"

        prompt = f"""{conversation_prefix}You are a document-based Q&A assistant. Answer the user's question directly and only from the provided context.

Context from documents:
{context}

User's Question: {query}

STRICT RULES:
1. Give a direct answer to the exact question asked.
2. Keep it brief: most answers should be 1-3 sentences.
3. Do NOT summarize the whole document unless the user explicitly asks for a summary.
4. Do NOT repeat large blocks of text or document content.
5. Use only information explicitly present in the context.
6. If the answer is missing from the context, say exactly: "Information not found in document."

Answer style:
- For factual questions, answer in one sentence with the fact.
- For explanation questions, give only the relevant part, no extra background.
- For follow-up questions, use the conversation history above to understand the reference but still answer directly.

Your final answer:"""

        try:
            last_error = None
            for model in get_llm_model_candidates():
                try:
                    agent_logger.info(f"{self.name}: 🤖 Invoking LLM - Model: {model}, Temperature: 0.2")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful research and document extraction assistant. You must provide accurate, well-structured answers based only on the context provided by the user. You MUST answer using ONLY the information in the context and never use your general knowledge. If the answer is not in the context, respond with: 'Information not found in document."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2
                    )

                    summary = response.choices[0].message.content

                    usage = response.usage
                    agent_logger.info(
                        f"{self.name}: ✅ LLM Response received | "
                        f"Tokens: {usage.prompt_tokens} input + {usage.completion_tokens} output = {usage.total_tokens} total | "
                        f"Response length: {len(summary)} chars"
                    )

                    return {
                        "status": "success",
                        "summary": summary,
                        "num_chunks_used": len(chunks)
                    }
                except Exception as e:
                    last_error = e
                    msg = str(e).lower()
                    if "model_not_found" not in msg and "does not exist" not in msg and "invalid_request_error" not in msg:
                        raise

            error_message = str(last_error) if last_error else "Unknown OpenAI model error"
            raise RuntimeError(f"No valid LLM model available. Last error: {error_message}")

        except Exception as e:
            agent_logger.error(f"{self.name}: Error during summarization: {str(e)}", exc_info=True)
            fallback_summary = "\n\n".join(chunks[:3]).strip()
            if not fallback_summary:
                fallback_summary = "I found relevant document content, but the OpenAI language model is currently unavailable. Please check your OpenAI credits or model access."
            return {
                "status": "success",
                "summary": fallback_summary,
                "num_chunks_used": len(chunks),
                "fallback": True
            }
