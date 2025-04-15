from huggingface_hub import InferenceClient
from config import BASE_MODEL, MY_MODEL, HF_TOKEN

class SchoolChatbot:
    """
    This class is extra scaffolding around a model. Modify this class to specify how the model recieves prompts and generates responses.

    Example usage:
        chatbot = SchoolChatbot()
        response = chatbot.get_response("What schools offer Spanish programs?")
    """

    def __init__(self):
        """
        Initialize the chatbot with a HF model ID
        """
        model_id = MY_MODEL if MY_MODEL else BASE_MODEL # define MY_MODEL in config.py if you create a new model in the HuggingFace Hub
        self.client = InferenceClient(model=model_id, token=HF_TOKEN)
        
    def format_prompt(self, user_input):
        """
        TODO: Implement this method to format the user's input into a proper prompt.
        
        This method should:
        1. Add any necessary system context or instructions
        2. Format the user's input appropriately
        3. Add any special tokens or formatting the model expects

        Args:
            user_input (str): The user's question about Boston schools

        Returns:
            str: A formatted prompt ready for the model
        
        Example prompt format:
            "You are a helpful assistant that specializes in Boston schools...
             User: {user_input}
             Assistant:"
        """
        context = (
            "You are a helpful assistant that specializes in helping parents choose Boston Public Schools"
            "Answer clearly and accurately using the latest school registration rules, deadlines, and program information."
            "Always be professional, clear, and focused on helping parents make informed decisions about schools.\n\n"
            "Key facts:\n"
                "- Registration is a 6-step process. Assistance is available in 10 languages via Welcome Centers or by calling 617-635-9010.\n"
                "- Welcome Centers:\n"
                "  • Dorchester: 1216 Dorchester Ave | M/T/Th/F 9–5, W 12–5 | 617-635-8015\n"
                "  • East Boston (Umana): 312 Border St | M/T 9–5, W 12–5 (Jan only) | 617-635-9597\n"
                "  • Roslindale: 515 Hyde Park Ave | M/T/Th/F 9–5, W 12–5 | 617-635-8040\n"
                "  • Roxbury: 2300 Washington St | M/T/Th/F 9–5, W 12–5 | 617-635-9010\n"
                "- School eligibility by grade (child must be age X by Sept 1, 2025): K0=3, K1=4, K2=5, Grade 1=6, ... Grade 12=17\n"
                "- To view eligible schools, use the School Choice Tool: https://boston.explore.avela.org/\n"
                "- Enter child’s grade, address, zip, and primary language. Eligible schools marked with green stars.\n"
                "- Home-Based plan assigns schools based on proximity + quality. Citywide and some regional options also available.\n"
                "- Special admission schools require separate applications + ranking in the registration form.\n"
                "- Required documents:\n"
                "  • Birth certificate/passport, immunization & physical exam, parent photo ID, 2 proofs of Boston residency\n"
                "- Optional docs: IEP (if applicable), high school transcript (recommended)\n"
                "- Pre-registration is optional but saves time: https://www.bostonpublicschools.org/pre-register\n"
                "- Final registration requires appointment: schedule online, call 617-635-9010, or visit a Welcome Center\n"
                "- Multilingual learners may need in-person language assessment at the Newcomers Assessment Counseling Center (NACC)\n"
        )
        return (
            f"{context}\n"
            f"User: {user_input}\n"
            "Assistant:"
        )
        
    def get_response(self, user_input):
        """
        TODO: Implement this method to generate responses to user questions.
        
        This method should:
        1. Use format_prompt() to prepare the input
        2. Generate a response using the model
        3. Clean up and return the response

        Args:
            user_input (str): The user's question about Boston schools

        Returns:
            str: The chatbot's response

        Implementation tips:
        - Use self.format_prompt() to format the user's input
        - Use self.client to generate responses
        """
        prompt = self.format_prompt(user_input)
        
        try:
            print("Generating response...")
            # TODO: revisit parameters later for formatting or prompt optimization. 
            response = self.client.text_generation(
                prompt,
                max_new_tokens=512,
                stop=["User:", "Assistant:"],
                do_sample=False, # better to have deterministic decoding 
                return_full_text=False
            )
            return response.strip()
            
        except Exception as e:
            print(f"API error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"


