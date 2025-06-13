import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from retriever import retrieve_top_k, filter_chunks, is_out_of_domain
from utils.prompt_loader import load_prompt
from utils.logger import log_interaction, log_error
from utils.feedback_logger import log_feedback


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


# Core function
def ask_chatbot(query, retrieved_chunks=None, k=5, strategy="cot"):
    if is_out_of_domain(query):
        return "I'm sorry, your question appears to be outside the scope of the provided document."

    if retrieved_chunks is None:
        retrieved_chunks = retrieve_top_k(query, k)

    context_chunks = filter_chunks(retrieved_chunks, max_tokens=4000)
    prompt = build_prompt(query, context_chunks, mode=strategy)

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        response_text = response.choices[0].message.content.strip()
        usage_data = response.usage if hasattr(response, 'usage') else None
        
        log_interaction(
            user_query=query,
            strategy=strategy,
            response=response_text,
            prompt_version="v1",
            model_name="gpt-4o-mini-voc2",
            tokens_used=usage_data.get("total_tokens") if usage_data else None
        )
        
        return response_text
    except Exception as e:
        log_error(str(e), context={"query": query, "strategy": strategy})
        return "An error occurred while processing your request."

# Example usage
if __name__ == "__main__":
    query = "What are the top 3 recommendations does the report make for retailers and brands?"
    strategy = "cot"
    prompt_version = "v1"
    model_name = "gpt-4o-mini-voc2"

    answer = ask_chatbot(query, strategy=strategy)

    print("\n🤖 Chatbot Answer:\n")
    print(answer)

    # Ask for feedback
    feedback = input("\nWas this answer helpful? (thumbs_up/thumbs_down): ").strip().lower()

    # Log feedback
    log_feedback(
        user_query=query,
        model_response=answer,
        strategy=strategy,
        prompt_version=prompt_version,
        model_name=model_name,
        feedback=feedback
    )
    print("✅ Feedback recorded. Thank you!")