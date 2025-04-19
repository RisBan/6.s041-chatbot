from huggingface_hub import InferenceClient
from config import BASE_MODEL, MY_MODEL, HF_TOKEN
from src.eligibility_api import EligibilityAPI
import re

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
        self.eligibility_api = EligibilityAPI()
        
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
                "- Enter child's grade, address, zip, and primary language. Eligible schools marked with green stars.\n"
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
    
    def extract_address_info(self, user_input):
        """
        Extract address information from user input using regex patterns.
        
        Args:
            user_input (str): The user's question or statement
            
        Returns:
            dict or None: Extracted address information or None if not found
        """
        # Look for complete addresses with street, city, state, zip
        address_pattern = r'(?:at|on|near|live(?:s)? (?:at|on|in|near))?\s*([0-9]+\s+[A-Za-z\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Terrace|Ter|Way)[.,]?)\s*(?:in)?\s*([A-Za-z\s]+)[.,]?\s*(?:MA|Massachusetts)[.,]?\s*(\d{5})'
        
        address_match = re.search(address_pattern, user_input, re.IGNORECASE)
        
        if address_match:
            return {
                "streetAddress": address_match.group(1).strip(),
                "streetAddressLine2": "",
                "city": address_match.group(2).strip(),
                "state": "MA",
                "zipCode": address_match.group(3).strip()
            }
        
        # Look for just a Boston neighborhood and zip code
        neighborhood_pattern = r'(?:in|near|from)\s+([A-Za-z\s]+(?:Plain|Hill|Square|Center|Bay|Park|Boston))\s*(?:area|neighborhood)?\s*(?:,\s*)?(?:\(?(?:zip(?:code)?)?\s*(\d{5})\)?)?'
        
        neighborhood_match = re.search(neighborhood_pattern, user_input, re.IGNORECASE)
        
        if neighborhood_match and neighborhood_match.group(2):
            return {
                "streetAddress": "",
                "streetAddressLine2": "",
                "city": "Boston",
                "state": "MA",
                "zipCode": neighborhood_match.group(2).strip()
            }
        
        # Look for just a zip code
        zip_pattern = r'(?:zip(?:code)?)?\s*(\d{5})'
        zip_match = re.search(zip_pattern, user_input, re.IGNORECASE)
        
        if zip_match:
            return {
                "streetAddress": "",
                "streetAddressLine2": "",
                "city": "Boston",
                "state": "MA",
                "zipCode": zip_match.group(1).strip()
            }
            
        return None
    
    def extract_grade_info(self, user_input):
        """
        Extract grade level information from user input.
        
        Args:
            user_input (str): The user's question or statement
            
        Returns:
            str or None: Grade ID or None if not found
        """
        grade_patterns = {
            "K0": r'\bK0\b|(?:3|three)[-\s]?year[-\s]?old',
            "K1": r'\bK1\b|(?:4|four)[-\s]?year[-\s]?old|pre[-\s]?k',
            "K2": r'\bK2\b|(?:5|five)[-\s]?year[-\s]?old|kindergarten',
        }
        
        grade_options = self.eligibility_api.grade_options()
        
        for grade, pattern in grade_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                return grade_options.get(grade)
                
        return grade_options.get("K2")  # Default to K2 if no grade detected
    
    def extract_language_info(self, user_input):
        """
        Extract language preference from user input.
        
        Args:
            user_input (str): The user's question or statement
            
        Returns:
            str: Language ID (defaults to English if not found)
        """
        language_patterns = {
            "Spanish": r'spanish|español',
            # Add other languages as needed
        }
        
        language_options = self.eligibility_api.language_options()
        
        for language, pattern in language_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                return language_options.get(language)
                
        return language_options.get("English")  # Default to English
        
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
        # Check if user is asking about eligible schools
        if re.search(r'what schools|eligible schools|available schools|school(?:s)? (?:for|near|in|around)', user_input, re.IGNORECASE):
            try:
                # Extract information needed for API
                address = self.extract_address_info(user_input)
                grade_id = self.extract_grade_info(user_input)
                language_id = self.extract_language_info(user_input)
                
                if address and grade_id:
                    # Call the API to find eligible schools
                    results = self.eligibility_api.find_eligible_schools(
                        grade_id=grade_id,
                        address=address,
                        language_id=language_id
                    )
                    
                    # Process results
                    eligible_schools = results.get("schools", [])
                    
                    if eligible_schools:
                        schools_info = "Based on your location and student information, these schools are available:\n\n"
                        for i, school in enumerate(eligible_schools[:10], 1):  # Limit to first 10 schools
                            schools_info += f"{i}. {school.get('name', 'Unknown School')}\n"
                            if school.get('address'):
                                schools_info += f"   Address: {school.get('address')}\n"
                            schools_info += "\n"
                        
                        # Add information about total eligible schools if more than 10
                        if len(eligible_schools) > 10:
                            schools_info += f"\nThere are {len(eligible_schools)} eligible schools in total. "
                            
                        schools_info += "For more details, please visit: https://boston.explore.avela.org/"
                        return schools_info
                    else:
                        return "I couldn't find any eligible schools for your location and student information. Please verify your address is in Boston and try again, or visit https://boston.explore.avela.org/ directly."
            except Exception as e:
                print(f"API error: {e}")
                # Fall back to model response if API fails
        
        # Default behavior: use the model
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


