import json
import pandas as pd  # Import pandas for DataFrame operations
from src.chat import SchoolChatbot

def load_questions(file_path):
    """Load questions and expected answers from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_chatbot_responses(questions_file, question_type="yes_no"):
    """
    Evaluate the chatbot's responses against expected answers.
    
    Args:
        questions_file (str): Path to the JSON file with questions and answers.
        question_type (str): Type of questions ("yes_no" or "multiple_choice").
    
    Returns:
        list: Evaluation results.
    """
    # Initialize the chatbot
    chatbot = SchoolChatbot()
    chatbot.reset_state() 

    # Load questions and expected answers
    questions = load_questions(questions_file)

    # Iterate through each question
    results = []
    for entry in questions:
        question = entry["question"]
        expected_answer = entry["answer"]

        # Modify the question for multiple-choice to include options and instructions
        if question_type == "multiple_choice" and "options" in entry:
            options = entry["options"]
            options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
            question = f"{question}\nOptions:\n{options_text}\nPlease start your answer with the correct letter (e.g., 'A', 'B')."

        # Get the chatbot's response
        response = chatbot.get_response(question)

        # Determine if the response matches the expected answer
        if question_type == "yes_no":
            is_correct = expected_answer.lower() in response.lower()
        elif question_type == "multiple_choice":
            is_correct = response.strip().upper().startswith(expected_answer.strip().upper())
        else:
            raise ValueError("Invalid question type. Use 'yes_no' or 'multiple_choice'.")

        result = 1 if is_correct else 0

        # Save the result
        results.append({
            "Question": question,
            "Expected Answer": expected_answer,
            "Chatbot Response": response,
            "Correct (1)/Incorrect (0)": result
        })

    return results

def main():
    
    # Specify the type of questions: "yes_no" or "multiple_choice"
    question_type = input("Enter question type ('yes_no' or 'multiple_choice'): ").strip()

    # Path to the JSON file with questions and expected answers
    questions_file = "chatbot_questions.json" if question_type == "yes_no" else "multimc_questions.json"

    # Evaluate the chatbot
    results = evaluate_chatbot_responses(questions_file, question_type)

    # Convert results to a Pandas DataFrame
    df = pd.DataFrame(results)

    # Save the DataFrame to a CSV file
    output_file = f"evaluation_results_{question_type}.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Results saved to {output_file}")

    # Print the results
    print(df)

if __name__ == "__main__":
    main()