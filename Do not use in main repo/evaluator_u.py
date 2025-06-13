import json
from bert_score import score as bert_score
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import re
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

# Azure OpenAI client for GPT-based evaluation
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15"
)
CHAT_MODEL = os.getenv("DEPLOYMENT_NAME")

# Load evaluation results
results_path = os.path.join(base_folder, "evaluation", "test_cases.json")
with open(results_path, "r", encoding="utf-8") as f:
    results = json.load(f)

# Function to extract concise factual answers
def extract_facts(text):
    # Extract percentages, numbers, and short phrases
    facts = re.findall(r'\b\d+%|\b\d+\b|(?:\b[A-Z][a-z]*\b\s?){1,3}', text)
    return ' '.join(facts)

# Function to evaluate using BERTScore
def evaluate_bertscore(results):
    references = [result['expected'] for result in results]
    candidates = [result['answer'] for result in results]
    P, R, F1 = bert_score(candidates, references, lang="en", rescale_with_baseline=True)
    return P.mean().item(), R.mean().item(), F1.mean().item()

# Function to evaluate using GPT-based evaluation
def evaluate_gpt(results):
    scores = []
    for result in results:
        prompt = f"""You are an evaluator. Given the query, expected answer, and the model's answer, rate the model's answer on a scale of 1 to 5 (1 being very poor, 5 being excellent) based on its correctness and relevance.

Query: {result['query']}
Expected Answer: {result['expected']}
Model's Answer: {result['answer']}

Rating (1-5):"""    
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )

        match = re.search(r'\b([1-5])\b', response.choices[0].message.content)
        rating = int(match.group(1)) if match else 0

        scores.append(rating)
    return sum(scores) / len(scores)

# Function to evaluate using exact match and fuzzy match
def evaluate_exact_fuzzy(results):
    exact_matches = 0
    fuzzy_scores = []
    for result in results:
        expected_facts = extract_facts(result['expected'])
        answer_facts = extract_facts(result['answer'])
        if expected_facts == answer_facts:
            exact_matches += 1
        fuzzy_scores.append(fuzz.ratio(expected_facts, answer_facts))
    exact_match_ratio = exact_matches / len(results)
    avg_fuzzy_score = sum(fuzzy_scores) / len(fuzzy_scores)
    return exact_match_ratio, avg_fuzzy_score

# Evaluate using BERTScore
bertscore_P, bertscore_R, bertscore_F1 = evaluate_bertscore(results)

# Evaluate using GPT-based evaluation
gpt_score = evaluate_gpt(results)

# Evaluate using exact match and fuzzy match
exact_match_ratio, avg_fuzzy_score = evaluate_exact_fuzzy(results)

# Print summary of all metrics
print(f"BERTScore - Precision: {bertscore_P:.4f}, Recall: {bertscore_R:.4f}, F1: {bertscore_F1:.4f}")
print(f"GPT-based Evaluation - Average Score: {gpt_score:.2f} / 5")
print(f"Exact Match Ratio: {exact_match_ratio:.4f}")
print(f"Average Fuzzy Score: {avg_fuzzy_score:.2f}")

# Save the evaluation summary
summary = {
    "BERTScore": {
        "Precision": bertscore_P,
        "Recall": bertscore_R,
        "F1": bertscore_F1
    },
    "GPT-based Evaluation": {
        "Average Score": gpt_score
    },
    "Exact Match Ratio": exact_match_ratio,
    "Average Fuzzy Score": avg_fuzzy_score
}
summary_path = os.path.join(base_folder, "evaluation", "evaluation_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(f"✅ Evaluation summary saved to {summary_path}")