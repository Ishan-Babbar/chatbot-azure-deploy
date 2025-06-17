import json
import os
import re
from openai import AzureOpenAI
import matplotlib.pyplot as plt
import pandas as pd
from fuzzywuzzy import fuzz
from bert_score import score as bert_score
from dotenv import load_dotenv
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu

# Import retriever and ask_chatbot functions
from src.retriever import retrieve_top_k
from src.chat_code import ask_chatbot

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

# Load test cases
results_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
with open(results_path, "r", encoding="utf-8") as f:
    test_cases = json.load(f)

# Function to extract concise factual answers
def extract_facts(text):
    facts = re.findall(r'\b\d+%|\b\d+\b|(?:\b[A-Z][a-z]*\b\s?){1,3}', text)
    return ' '.join(facts)

# Function to evaluate using BERTScore
def evaluate_bertscore(results):
    references = [result['expected'] for result in results]
    candidates = [result['answer'] for result in results]
    P, R, F1 = bert_score(candidates, references, lang="en", rescale_with_baseline=True)
    return P.mean().item(), R.mean().item(), F1.mean().item()

# # Function to evaluate using GPT-based evaluation
# def evaluate_gpt(results):
#     scores = []
#     for result in results:
#         prompt = f"""You are an evaluator. Given the query, expected answer, and the model's answer, rate the model's answer on a scale of 1 to 5 (1 being very poor, 5 being excellent) based on its correctness and relevance.

# Query: {result['query']}
# Expected Answer: {result['expected']}
# Model's Answer: {result['answer']}

# Rating (1-5):"""
#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": "You are an evaluator."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.0,
#             max_tokens=10
#         )

#         match = re.search(r'\b([1-5])\b', response.choices[0].message.content)
#         rating = int(match.group(1)) if match else 0

#         scores.append(rating)
#     return sum(scores) / len(scores)

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

# Function to evaluate using BLEU
def evaluate_bleu(results):
    scores = []
    for result in results:
        reference = result['expected'].split()
        candidate = result['answer'].split()
        score = sentence_bleu([reference], candidate)
        scores.append(score)
    return sum(scores) / len(scores)

# Function to evaluate using ROUGE-L
def evaluate_rouge(results):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = []
    for result in results:
        score = scorer.score(result['answer'], result['expected'])['rougeL'].fmeasure
        scores.append(score)
    return sum(scores) / len(scores)

# Generate answers using retriever and chatbot
for test_case in test_cases:
    query = test_case['query']
    retrieved_chunks = retrieve_top_k(query, k=5)
    answer = ask_chatbot(query, retrieved_chunks)
    test_case['answer'] = answer

# Evaluate using BERTScore
bertscore_P, bertscore_R, bertscore_F1 = evaluate_bertscore(test_cases)

# Evaluate using GPT-based evaluation
# gpt_score = evaluate_gpt(test_cases)

# Evaluate using exact match and fuzzy match
exact_match_ratio, avg_fuzzy_score = evaluate_exact_fuzzy(test_cases)

# Evaluate using BLEU
bleu_score = evaluate_bleu(test_cases)

# Evaluate using ROUGE-L
rouge_l_score = evaluate_rouge(test_cases)

# Print summary of all metrics
print(f"BERTScore - Precision: {bertscore_P:.4f}, Recall: {bertscore_R:.4f}, F1: {bertscore_F1:.4f}")
# print(f"GPT-based Evaluation - Average Score: {gpt_score:.2f} / 5")
print(f"Exact Match Ratio: {exact_match_ratio:.4f}")
print(f"Average Fuzzy Score: {avg_fuzzy_score:.2f}")
print(f"BLEU Score: {bleu_score:.4f}")
print(f"ROUGE-L Score: {rouge_l_score:.4f}")

# Save the evaluation summary
summary = {
    "BERTScore": {
        "Precision": bertscore_P,
        "Recall": bertscore_R,
        "F1": bertscore_F1
    },
    "GPT-based Evaluation": {
        # "Average Score": gpt_score
    },
    "Exact Match Ratio": exact_match_ratio,
    "Average Fuzzy Score": avg_fuzzy_score,
    "BLEU Score": bleu_score,
    "ROUGE-L Score": rouge_l_score
}
summary_path = os.path.join(os.path.dirname(__file__), "evaluation_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(f"✅ Evaluation summary saved to {summary_path}")

# Save detailed results to Excel
df = pd.DataFrame(test_cases)
excel_path = os.path.join(os.path.dirname(__file__), "evaluation_results.xlsx")
df.to_excel(excel_path, index=False)
print(f"✅ Detailed results saved to {excel_path}")

# Generate bar chart for visual comparison
# metrics = ["BERTScore F1", "GPT Score", "Exact Match Ratio", "Fuzzy Score", "BLEU Score", "ROUGE-L Score"]
metrics = ["BERTScore F1", "Exact Match Ratio", "Fuzzy Score", "BLEU Score", "ROUGE-L Score"]
# values = [bertscore_F1, gpt_score, exact_match_ratio, avg_fuzzy_score, bleu_score, rouge_l_score]
values = [bertscore_F1, exact_match_ratio, avg_fuzzy_score, bleu_score, rouge_l_score]

plt.figure(figsize=(10, 6))
plt.bar(metrics, values, color=['blue', 'green', 'red', 'purple', 'orange'])
# plt.bar(metrics, values, color=['blue', 'green', 'red', 'purple', 'orange', 'cyan'])
plt.xlabel('Metrics')
plt.ylabel('Scores')
plt.title('Evaluation Metrics Comparison')
plt_path = os.path.join(os.path.dirname(__file__), "evaluation_metrics_comparison.png")
plt.savefig(plt_path)
plt.show()
print(f"✅ Bar chart saved to {plt_path}")