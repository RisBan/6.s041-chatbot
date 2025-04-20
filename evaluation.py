import json
from src.chat import SchoolChatbot

def load_questions(file_path):
    """Load questions and expected answers from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_chatbot_responses(questions_file):
    """Evaluate the chatbot's responses against expected answers."""
    # Initialize the chatbot
    chatbot = SchoolChatbot()

    # Load questions and expected answers
    questions = load_questions(questions_file)

    # Iterate through each question
    results = []
    for entry in questions:
        question = entry["question"]
        expected_answer = entry["answer"]

        # Get the chatbot's response
        response = chatbot.get_response(question)

        # Determine if the response matches the expected answer
        if expected_answer.lower() in response.lower():
            result = "Correct"
        else:
            result = "Incorrect"

        # Save the result
        results.append({
            "question": question,
            "expected_answer": expected_answer,
            "chatbot_response": response,
            "result": result
        })

    return results

def main():
    # Path to the JSON file with questions and expected answers
    questions_file = "chatbot_questions.json"

    # Evaluate the chatbot
    results = evaluate_chatbot_responses(questions_file)

    # Print the results
    for result in results:
        print(f"Question: {result['question']}")
        print(f"Expected Answer: {result['expected_answer']}")
        print(f"Chatbot Response: {result['chatbot_response']}")
        print(f"Result: {result['result']}")
        print("-" * 50)

if __name__ == "__main__":
    main()