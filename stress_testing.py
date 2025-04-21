import json
from src.chat import SchoolChatbot

def test_chatbot():
    """
    Test the chatbot with specific edge cases.
    """
    # Initialize the chatbot
    chatbot = SchoolChatbot()

    # Define test cases
    test_cases = [
        {
            "description": "Address not in MA",
            "question": "Which schools can I enroll in if I live in 314 W 58th St, New York, NY 10019?",
            "expected_answer": "No"
        },
        {
            "description": "Address on border of two schools",
            "question": "If a family's address is on the border of two school zones, how is the school assignment determined?",
            "expected_answer": "Based on the home-based assignment plan."
        },
        {
            "description": "Fake grade (14th grade)",
            "question": "Can a student enroll in 14th grade in BPS?",
            "expected_answer": "No"
        },
    ]

    # Run test cases
    results = []
    for case in test_cases:
        question = case["question"]
        expected_answer = case["expected_answer"]

        # Get the chatbot's response
        response = chatbot.get_response(question)

        # Determine if the response matches the expected answer
        is_correct = expected_answer.lower() in response.lower()
        result = {
            "Description": case["description"],
            "Question": question,
            "Expected Answer": expected_answer,
            "Chatbot Response": response,
            "Correct (1)/Incorrect (0)": 1 if is_correct else 0
        }
        results.append(result)

    # Print results
    for result in results:
        print(f"Test Case: {result['Description']}")
        print(f"Question: {result['Question']}")
        print(f"Expected Answer: {result['Expected Answer']}")
        print(f"Chatbot Response: {result['Chatbot Response']}")
        print(f"Correct: {result['Correct (1)/Incorrect (0)']}")
        print("-" * 50)

if __name__ == "__main__":
    test_chatbot()