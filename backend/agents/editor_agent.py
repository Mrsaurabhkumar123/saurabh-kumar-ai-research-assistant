"""
Editor Agent: Refines and polishes the final answer based on critic feedback
"""
import os
from openai import OpenAI
from config import get_llm_model, get_llm_model_candidates
from utils.logger import agent_logger


class EditorAgent:
    def __init__(self):
        self.name = "Editor Agent"
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        agent_logger.info(f"{self.name} initialized")

    def edit(self, query: str, summary: str, critique: str, chunks: list[str]):
        """
        Polish the summary based on critic feedback

        Args:
            query: Original user question
            summary: Initial summary from SummarizerAgent
            critique: Feedback from CriticAgent
            chunks: Original retrieved chunks for additional context

        Returns:
            dict with final polished answer
        """
        agent_logger.info(f"{self.name}: Starting editing for query='{query}'")
        agent_logger.debug(f"{self.name}: Summary length: {len(summary)} chars, Critique length: {len(critique)} chars")

        if not summary:
            agent_logger.warning(f"{self.name}: No summary provided for editing")
            return {
                "status": "error",
                "message": "No summary to edit",
                "final_answer": ""
            }

        # Provide additional context for refinement
        context = "\n\n---\n\n".join(chunks)

        prompt = f"""You are an editor. Refine the answer to ensure it uses ONLY information from the document context.

Original Question: {query}

Initial Answer:
{summary}

Feedback:
{critique}

Document Context (THE ONLY SOURCE OF TRUTH):
{context}

CRITICAL RULES:
1. Use ONLY information from the Document Context above
2. If feedback mentions "hallucination" or "not in document", REMOVE that information
3. If feedback mentions missing info that IS in context, ADD it
4. DO NOT use general knowledge or external information
5. When in doubt, quote directly from the context

FOR SIMPLE QUESTIONS:
- Keep answer SHORT (1-2 sentences)
- Use exact wording from context when possible
- No extra explanations beyond what's in the context

FOR COMPLEX QUESTIONS:
- Provide comprehensive answer using ALL relevant info from context
- Do not add external examples or explanations
- Organize clearly, but content must come from context only

If the context doesn't contain enough information to fully answer the question, state: "Based on the document: [answer with available info]. Additional details not found in document."

Provide the corrected final answer (strictly from context):"""

        try:
            last_error = None
            for model in get_llm_model_candidates():
                try:
                    agent_logger.info(f"{self.name}: 🤖 Invoking LLM - Model: {model}, Temperature: 0.3")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert editor who creates clear, comprehensive, and well-structured answers."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )

                    final_answer = response.choices[0].message.content

                    usage = response.usage
                    agent_logger.info(
                        f"{self.name}: ✅ LLM Response received | "
                        f"Tokens: {usage.prompt_tokens} input + {usage.completion_tokens} output = {usage.total_tokens} total | "
                        f"Final answer length: {len(final_answer)} chars"
                    )

                    return {
                        "status": "success",
                        "final_answer": final_answer,
                        "editing_applied": True
                    }
                except Exception as e:
                    last_error = e
                    msg = str(e).lower()
                    if "model_not_found" not in msg and "does not exist" not in msg and "invalid_request_error" not in msg:
                        raise

            error_message = str(last_error) if last_error else "Unknown OpenAI model error"
            raise RuntimeError(f"No valid LLM model available. Last error: {error_message}")

        except Exception as e:
            agent_logger.error(f"{self.name}: Error during editing, using original summary: {str(e)}", exc_info=True)
            return {
                "status": "warning",
                "message": "The configured OpenAI model is unavailable. Using the latest available content without final model refinement.",
                "final_answer": summary,
                "editing_applied": False
            }
