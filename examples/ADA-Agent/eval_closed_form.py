import json
import argparse
import re
import os

from utils.utils import read_jsonl


# Function to extract formatted text using regular expressions
def extract_format(input_string):
    pattern = r"@(\w+)\[(.*?)\]"
    matches = re.findall(pattern, input_string)
    answer_names = [match[0] for match in matches]
    answers = [match[1] for match in matches]
    return answer_names, answers


def is_equal(response, label):
    if response == label:
        return True
    else:
        try:
            return abs(float(response) - float(label)) < 1e-6
        except:
            return False


# Function to evaluate responses with the adjusted label structure
def evaluate_responses(labels, responses):
    results = []
    for label in labels:
        label_id = label["id"]
        label_answers = {ans[0]: ans[1] for ans in label["common_answers"]}

        corresponding_response = next(
            (resp for resp in responses if "id" in resp.keys() and resp['response'] and resp["id"] == label_id), None)
        if corresponding_response:
            answer_names, answers = extract_format(corresponding_response["response"])
            extracted_answers = dict(zip(answer_names, answers))
            correct_answers = {ans_name: is_equal(extracted_answers.get(ans_name), label_answers[ans_name]) for ans_name
                               in label_answers.keys()}
            result = {
                "id": label_id,
                "label_answers": label_answers,
                "predicted_answers": extracted_answers,
                "correctness": correct_answers
            }
            results.append(result)
    return results


# Function to read concepts data from a JSONL file
def read_concepts_from_file(file_name):
    concepts_data = {}
    with open(file_name, 'r') as file:
        for line in file:
            question_data = json.loads(line.rstrip('\n'))
            question_id = question_data["id"]
            concepts = question_data["concepts"]
            concepts_data[question_id] = concepts
    return concepts_data


# Function to analyze concept accuracy
def analyze_concepts_accuracy(results, concepts_data):
    concept_accuracy = {}
    for result in results:
        question_id = result["id"]
        if question_id in concepts_data:
            for concept in concepts_data[question_id]:
                if concept not in concept_accuracy:
                    concept_accuracy[concept] = {"total": 0, "correct": 0}
                concept_accuracy[concept]["total"] += 1
                if 'correctness' in result and all(result['correctness'].values()):
                    concept_accuracy[concept]["correct"] += 1
    return {concept: round(acc["correct"] / acc["total"], 4) for concept, acc in concept_accuracy.items()}


def analyze_concepts_count_accuracy(results, concepts_data):
    concept_count_accuracy = {}
    two_or_more_concepts_accuracy = {"total": 0, "correct": 0}

    for result in results:
        question_id = result["id"]
        if question_id in concepts_data:
            concept_count = len(concepts_data[question_id])
            if concept_count not in concept_count_accuracy:
                concept_count_accuracy[concept_count] = {"total": 0, "correct": 0}
            concept_count_accuracy[concept_count]["total"] += 1

            if 'correctness' in result and all(result['correctness'].values()):
                concept_count_accuracy[concept_count]["correct"] += 1
            if concept_count >= 2:
                two_or_more_concepts_accuracy["total"] += 1
                if 'correctness' in result and all(result['correctness'].values()):
                    two_or_more_concepts_accuracy["correct"] += 1

    concept_count_accuracy = {count: round(acc["correct"] / acc["total"], 4) for count, acc in
                              concept_count_accuracy.items() if
                              acc["total"] > 0}
    if two_or_more_concepts_accuracy["total"] > 0:
        two_or_more_concepts_accuracy = round(two_or_more_concepts_accuracy["correct"] / two_or_more_concepts_accuracy[
            "total"], 4)
    else:
        two_or_more_concepts_accuracy = None

    return concept_count_accuracy, two_or_more_concepts_accuracy


# Functions to evaluate accuracy
def evaluate_accuracy_by_question(results):
    correct = sum('correctness' in result and all(result['correctness'].values()) for result in results)
    total = len(results)
    return round(correct / total, 4) if total > 0 else 0


def evaluate_accuracy_by_sub_question(results):
    correct = sum(sum(result['correctness'].values()) for result in results if 'correctness' in result)
    total = sum(len(result['correctness']) for result in results if 'correctness' in result)
    return round(correct / total, 4) if total > 0 else 0


def evaluate_accuracy_proportional_by_sub_question_adjusted(results):
    total_score = 0
    for result in results:
        if 'correctness' in result:
            sub_question_count = len(result['correctness'])
            score_per_sub_question = 1 / sub_question_count if sub_question_count > 0 else 0
            question_score = sum(result['correctness'].values()) * score_per_sub_question
            total_score += question_score
    return round(total_score / len(results), 4) if results else 0


# Main function to run the evaluation
def main():
    parser = argparse.ArgumentParser(description="Evaluate closed-form dataset responses.")
    parser.add_argument('--questions_file_path', type=str, default="data/da-dev-questions.jsonl",
                        help='Path to the questions file (JSONL format)')
    parser.add_argument('--labels_file_path', type=str, default="data/da-dev-labels.jsonl",
                        help='Path to the labels file (JSONL format)')
    parser.add_argument('--responses_file_path', type=str, required=True,
                        help='Path to the responses file (JSONL format)')
    args = parser.parse_args()

    os.makedirs("eval_outputs", exist_ok=True)

    # Reading files
    labels = read_jsonl(args.labels_file_path)
    responses = read_jsonl(args.responses_file_path)
    concepts_data = read_concepts_from_file(args.questions_file_path)

    # Evaluating responses
    results = evaluate_responses(labels, responses)

    # Calculate accuracies
    accuracy_by_question = evaluate_accuracy_by_question(results)
    accuracy_by_sub_question = evaluate_accuracy_by_sub_question(results)
    accuracy_proportional_by_sub_question = evaluate_accuracy_proportional_by_sub_question_adjusted(results)

    # Print results
    print(f"Accuracy by Question: {accuracy_by_question:.2%}")
    print(f"Accuracy Proportional by Sub-Question: {accuracy_proportional_by_sub_question:.2%}")
    print(f"Accuracy by Sub-Question: {accuracy_by_sub_question:.2%}")
    main_results = {"Accuracy by Question": accuracy_by_question,
                    "Accuracy Proportional by Sub-Question": accuracy_proportional_by_sub_question,
                    "Accuracy by Sub-Question": accuracy_by_sub_question}

    # Analyzing concepts accuracy
    concept_accuracy_analysis = analyze_concepts_accuracy(results, concepts_data)

    # Analyzing concepts count accuracy
    concept_count_accuracy_analysis, two_or_more_concepts_accuracy = analyze_concepts_count_accuracy(results,
                                                                                                     concepts_data)

    # Print results
    print("Concept Accuracy Analysis:")
    for concept, accuracy in concept_accuracy_analysis.items():
        print(f"{concept}: {accuracy:.2%}")

    print("\nConcept Count Accuracy Analysis:")
    for count, accuracy in concept_count_accuracy_analysis.items():
        print(f"{count} Concept(s): {accuracy:.2%}")

    # Print accuracy for questions with >= 2 concepts
    if two_or_more_concepts_accuracy is not None:
        print(f"\nAccuracy for Questions with >= 2 Concepts: {two_or_more_concepts_accuracy:.2%}")
    else:
        print("\nNo data available for questions with >= 2 Concepts.")

    responses_file_name = os.path.splitext(os.path.basename(args.responses_file_path))[0]
    eval_file_name = f'eval_outputs/{responses_file_name}_evaluation_analysis.json'

    with open(eval_file_name, 'w') as file:
        json.dump({
            "main_results": main_results,
            "concept_accuracy_analysis": concept_accuracy_analysis,
            "concept_count_accuracy_analysis": concept_count_accuracy_analysis,
            "two_or_more_concepts_accuracy": two_or_more_concepts_accuracy
        }, file, indent=4)


if __name__ == "__main__":
    main()
