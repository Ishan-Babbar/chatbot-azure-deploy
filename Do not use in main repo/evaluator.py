import os
import json
from dotenv import load_dotenv
from app.chat_code import ask_chatbot
from app.retriever import retrieve_top_k
from rouge import Rouge
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import matplotlib.pyplot as plt

"""
Improvements Made
-Added BLEU smoothing for better stability on short answers.
-Modularized scoring functions for future integration of BLEURT, BERTScore, or GPT-based evals.
-Default strategy changed to "cot" for better synthesis.
-Improved error handling for ROUGE.

"""

# Load environment variables
load_dotenv()
base_folder = os.getenv("BASE_FOLDER_PATH")

# Initialize scorers
rouge = Rouge()
smoothie = SmoothingFunction().method4

def compute_bleu(reference, hypothesis):
    reference = [reference.split()]
    hypothesis = hypothesis.split()
    return sentence_bleu(reference, hypothesis, smoothing_function=smoothie)

def compute_rouge(reference, hypothesis):
    try:
        return rouge.get_scores(hypothesis, reference)[0]['rouge-l']['f']
    except Exception:
        return 0.0

def evaluate(test_cases, strategy="cot", k=10):
    results = []
    for case in test_cases:
        query = case["query"]
        expected = case["expected"]
        retrieved = retrieve_top_k(query, k)
        answer = ask_chatbot(query, k=k, strategy=strategy)
        bleu_score = compute_bleu(expected, answer)
        rouge_score = compute_rouge(expected, answer)
        results.append({
            "query": query,
            "expected": expected,
            "answer": answer,
            "retrieved_chunks": retrieved,
            "bleu_score": bleu_score,
            "rouge_score": rouge_score
        })
    return results

def visualize_results(results, output_path):
    queries = [result['query'] for result in results]
    bleu_scores = [result['bleu_score'] for result in results]
    rouge_scores = [result['rouge_score'] for result in results]
    x = range(len(queries))

    plt.figure(figsize=(12, 6))
    plt.bar(x, bleu_scores, width=0.4, label='BLEU', align='center')
    plt.bar(x, rouge_scores, width=0.4, label='ROUGE', align='edge')
    plt.xlabel('Queries')
    plt.ylabel('Scores')
    plt.title('Evaluation Scores')
    plt.xticks(x, queries, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()

if __name__ == "__main__":
    test_cases = [
        {"query": "What percentage of Gen Z consumers use generative AI in shopping?", "expected": "45% of Gen Z consumers use generative AI in shopping."},
        {"query": "What are the key consumer clusters identified in the report?", "expected": "The report identifies clusters such as tech-savvy consumers, sustainability-focused consumers, and value-driven consumers."},
        {"query": "How is sustainability influencing consumer behavior?", "expected": "Sustainability is a major factor influencing consumer behavior, with many consumers preferring brands that are environmentally friendly and socially responsible."},
        {"query": "What role does social commerce play in consumer trends?", "expected": "Social commerce is becoming increasingly important, with consumers using social media platforms to discover and purchase products."},
        {"query": "What are the main reasons consumers switch brands?", "expected": "Consumers switch brands mainly due to lack of personalization, better experience offered by competitors, and dissatisfaction with current brand."},
        {"query": "How are brands leveraging generative AI?", "expected": "Brands are leveraging generative AI for personalized marketing, product recommendations, and enhancing customer experience."},
        {"query": "What is the impact of Gen Z on consumer trends?", "expected": "Gen Z is significantly impacting consumer trends with their preference for digital experiences, sustainability, and social commerce."},
        {"query": "How important is personalization in consumer trends?", "expected": "Personalization is extremely important, with consumers expecting tailored experiences and recommendations."},
        {"query": "What are the future predictions for consumer behavior?", "expected": "Future predictions include increased use of AI, greater emphasis on sustainability, and more integration of social commerce."},
        {"query": "How are consumers responding to brand transparency?", "expected": "Consumers are responding positively to brand transparency, valuing honesty and openness about products and practices."}
    ]

    results = evaluate(test_cases)
    output_path = os.path.join(base_folder, "evaluation", "results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Evaluation results saved to {output_path}")

    chart_path = os.path.join(base_folder, "evaluation", "evaluation_chart.png")
    visualize_results(results, chart_path)
    print(f"📊 Evaluation chart saved to {chart_path}")