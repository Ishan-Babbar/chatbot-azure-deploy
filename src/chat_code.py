import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import sys
import os
# Ensure the parent directory is in the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.prompt_loader import load_prompt
from utils.feedback_logger import log_feedback
from utils.logger import log_interaction, log_error
from retriever import retrieve_top_k, filter_chunks, is_out_of_domain


# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

# Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)
CHAT_MODEL = os.getenv("DEPLOYMENT_NAME")

# Prompt templates - Load from Utils
def build_prompt(query, context_chunks, mode="default", version="v1"):
    prompt_data = load_prompt(version)
    strategies = prompt_data["strategies"]
    
    if mode not in strategies:
        mode = "default"
    
    template = strategies[mode]["template"]
    context = "\n\n".join(chunk["text"] for chunk in context_chunks)
    
    return template.format(context=context, query=query)


# Core function with memory and reference tagging
def ask_chatbot(query, chat_history=None, retrieved_chunks=None, k=5, strategy="cot"):
    if is_out_of_domain(query):
        return {
            "reply": "I'm sorry, your question appears to be outside the scope of the provided document.",
            "references": []
        }

    if query.lower().strip().endswith("?") and len(query.split()) < 6:
        strategy = "casual"

    if retrieved_chunks is None:
        retrieved_chunks = retrieve_top_k(query, k)

    context_chunks = filter_chunks(retrieved_chunks, max_tokens=4000)

    # Build reference map
    references = []
    reference_map = {}
    for idx, chunk in enumerate(context_chunks, start=1):
        ref = {
            "id": idx,
            "title": chunk.get("title", f"Source {idx}"),
            "url": chunk.get("source", "#")
        }
        references.append(ref)
        reference_map[chunk["text"]] = idx

    # Build prompt
    prompt = build_prompt(query, context_chunks, mode=strategy)

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=800
        )
        response_text = response.choices[0].message.content.strip()

        # Append reference tags at the end
        ref_tags = " ".join([f"[{ref['id']}]" for ref in references])
        response_with_refs = f"{response_text} {ref_tags}".strip()

        usage_data = response.usage if hasattr(response, 'usage') else None
        log_interaction(
            user_query=query,
            strategy=strategy,
            response=response_text,
            prompt_version="v1",
            model_name="gpt-4o-mini-voc2",
            tokens_used=usage_data.total_tokens if usage_data else None
        )

        return {
            "reply": response_with_refs,
            "references": references
        }

    except Exception as e:
        log_error(str(e), context={"query": query, "strategy": strategy})
        return {
            "reply": "An error occurred while processing your request.",
            "references": []
        }

# # Example usage
# if __name__ == "__main__":
#     query = "What are the top 3 recommendations does the report make for retailers and brands?"
#     strategy = "cot"
#     prompt_version = "v1"
#     model_name = "gpt-4o-mini-voc2"

#     answer = ask_chatbot(query, strategy=strategy)

#     print("\n🤖 Chatbot Answer:\n")
#     print(answer)

#     # Ask for feedback
#     feedback = input("\nWas this answer helpful? (thumbs_up/thumbs_down): ").strip().lower()

#     # Log feedback
#     log_feedback(
#         user_query=query,
#         model_response=answer,
#         strategy=strategy,
#         prompt_version=prompt_version,
#         model_name=model_name,
#         feedback=feedback
#     )
#     print("✅ Feedback recorded. Thank you!")