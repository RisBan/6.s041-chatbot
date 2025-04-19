from huggingface_hub import InferenceClient
from config import BASE_MODEL, MY_MODEL, HF_TOKEN
from src.eligibility_api import EligibilityAPI
import re
import json

class SchoolChatbot:
    """
    This class is extra scaffolding around a model. Modify this class to specify how the model recieves prompts and generates responses.

    Example usage:
        chatbot = SchoolChatbot()
        response = chatbot.get_response("What schools offer Spanish programs?")
    """

    def __init__(self):
        """
        Initialize the chatbot with a HF model ID and conversation state
        """
        model_id = MY_MODEL if MY_MODEL else BASE_MODEL # define MY_MODEL in config.py if you create a new model in the HuggingFace Hub
        self.client = InferenceClient(model=model_id, token=HF_TOKEN)
        self.eligibility_api = EligibilityAPI()
        self.conversation_state = {}
        self.reset_state()
    
    def reset_state(self):
        """Reset the conversation state to default values"""
        self.conversation_state = {
            "address": None,              # User's address information
            "grade": None,                # Grade/age of the child
            "language": None,             # Language preference
            "waiting_for": None,          # What we're waiting for the user to provide
            "last_question": None,        # Last question we asked the user
            "last_school_results": None,  # Last school results we found
            "context": {}                 # Additional context for the conversation
        }
    
    def save_to_context(self, key, value):
        """Save a value to the conversation context"""
        self.conversation_state["context"][key] = value
    
    def get_from_context(self, key, default=None):
        """Get a value from the conversation context"""
        return self.conversation_state["context"].get(key, default)
    
    def format_prompt(self, user_input, history=None):
        """
        Format the user's input into a proper prompt with conversation history.
        
        Args:
            user_input (str): The user's question about Boston schools
            history (list, optional): Previous conversation history

        Returns:
            str: A formatted prompt ready for the model
        """
        context = """You are a helpful assistant that specializes in helping parents choose Boston Public Schools. 
Answer clearly and accurately using the latest school registration rules, deadlines, and program information. 
Always be professional, clear, and focused on helping parents make informed decisions about schools.

Key facts:
- Registration is a 6-step process. Assistance is available in 10 languages via Welcome Centers or by calling 617-635-9010.
- Welcome Centers:
  • Dorchester: 1216 Dorchester Ave | M/T/Th/F 9–5, W 12–5 | 617-635-8015
  • East Boston (Umana): 312 Border St | M/T 9–5, W 12–5 (Jan only) | 617-635-9597
  • Roslindale: 515 Hyde Park Ave | M/T/Th/F 9–5, W 12–5 | 617-635-8040
  • Roxbury: 2300 Washington St | M/T/Th/F 9–5, W 12–5 | 617-635-9010
- School eligibility by grade (child must be age X by Sept 1, 2025): K0=3, K1=4, K2=5, Grade 1=6, ... Grade 12=17
- To view eligible schools, use the School Choice Tool: https://boston.explore.avela.org/
- Enter child's grade, address, zip, and primary language. Eligible schools marked with green stars.
- Home-Based plan assigns schools based on proximity + quality. Citywide and some regional options also available.
- Special admission schools require separate applications + ranking in the registration form.
- Required documents:
  • Birth certificate/passport, immunization & physical exam, parent photo ID, 2 proofs of Boston residency
- Optional docs: IEP (if applicable), high school transcript (recommended)
- Pre-registration is optional but saves time: https://www.bostonpublicschools.org/pre-register
- Final registration requires appointment: schedule online, call 617-635-9010, or visit a Welcome Center
- Multilingual learners may need in-person language assessment at the Newcomers Assessment Counseling Center (NACC)
"""
        # Add conversation history if provided
        if history and len(history) > 0:
            conversation = "\n\nConversation history:\n"
            for user_msg, assistant_msg in history:
                conversation += f"User: {user_msg}\nAssistant: {assistant_msg}\n"
            context += conversation
        
        # Add information we've collected about the user
        user_info = "\n\nWhat I know about the user:\n"
        if self.conversation_state["address"]:
            addr = self.conversation_state["address"]
            address_str = f"{addr.get('streetAddress', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zipCode', '')}"
            user_info += f"- Address: {address_str.strip()}\n"
        
        if self.conversation_state["grade"]:
            user_info += f"- Child's grade: {self.conversation_state.get('grade_display', 'Unknown')}\n"
            
        if self.conversation_state["language"]:
            user_info += f"- Language preference: {self.conversation_state.get('language_display', 'Unknown')}\n"
            
        if any([self.conversation_state["address"], self.conversation_state["grade"], self.conversation_state["language"]]):
            context += user_info
        
        # Final formatted prompt
        return f"{context}\n\nUser: {user_input}\nAssistant:"
    
    def extract_address_info(self, user_input):
        """
        Extract address information from user input using regex patterns.
        
        Args:
            user_input (str): The user's question or statement
            
        Returns:
            dict or None: Extracted address information or None if not found
        """
        # If we're explicitly waiting for an address, be more lenient with parsing
        if self.conversation_state["waiting_for"] == "address":
            # For direct address responses, we can be more lenient
            simple_address_pattern = r'([0-9]+\s+[A-Za-z\s.]+)(?:,\s*|\s+)([A-Za-z\s]+)(?:,\s*|\s+)(?:MA|Massachusetts)(?:,\s*|\s+)(\d{5})'
            simple_match = re.search(simple_address_pattern, user_input, re.IGNORECASE)
            if simple_match:
                return {
                    "streetAddress": simple_match.group(1).strip(),
                    "streetAddressLine2": "",
                    "city": simple_match.group(2).strip(),
                    "state": "MA",
                    "zipCode": simple_match.group(3).strip()
                }
            
            # Handle just the zip code case more aggressively
            zip_only = re.search(r'(\d{5})', user_input)
            if zip_only:
                return {
                    "streetAddress": "",
                    "streetAddressLine2": "",
                    "city": "Boston",
                    "state": "MA",
                    "zipCode": zip_only.group(1).strip()
                }
        
        # Standard address patterns for regular queries
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
        # If we're explicitly waiting for a grade, be more lenient
        if self.conversation_state["waiting_for"] == "grade":
            # For direct grade responses like "5" or "grade 5" or "fifth grade"
            simple_grade_pattern = r'(?:grade\s*)?(\d{1,2})(?:th|st|nd|rd)?(?:\s*grade)?'
            simple_match = re.search(simple_grade_pattern, user_input, re.IGNORECASE)
            if simple_match:
                grade = simple_match.group(1)
                grade_options = self.eligibility_api.grade_options()
                if grade in grade_options:
                    self.conversation_state["grade_display"] = f"Grade {grade}"
                    return grade_options.get(grade)
            
            # Handle kindergarten responses more directly
            if re.search(r'k(?:indergarten)?[\s-]*0', user_input, re.IGNORECASE):
                self.conversation_state["grade_display"] = "Kindergarten 0 (K0)"
                return self.eligibility_api.grade_options().get("K0")
            if re.search(r'k(?:indergarten)?[\s-]*1', user_input, re.IGNORECASE):
                self.conversation_state["grade_display"] = "Kindergarten 1 (K1)"
                return self.eligibility_api.grade_options().get("K1")
            if re.search(r'k(?:indergarten)?[\s-]*2|kindergarten', user_input, re.IGNORECASE):
                self.conversation_state["grade_display"] = "Kindergarten 2 (K2)"
                return self.eligibility_api.grade_options().get("K2")
        
        # Define regex patterns for different grades
        grade_patterns = {
            "K0": r'\bK0\b|(?:3|three)[-\s]?year[-\s]?old|grade k0',
            "K1": r'\bK1\b|(?:4|four)[-\s]?year[-\s]?old|pre[-\s]?k|grade k1',
            "K2": r'\bK2\b|(?:5|five)[-\s]?year[-\s]?old|kindergarten|grade k2',
            "1": r'\bgrade 1\b|(?:1st|first) grade|(?:6|six)[-\s]?year[-\s]?old',
            "2": r'\bgrade 2\b|(?:2nd|second) grade|(?:7|seven)[-\s]?year[-\s]?old',
            "3": r'\bgrade 3\b|(?:3rd|third) grade|(?:8|eight)[-\s]?year[-\s]?old',
            "4": r'\bgrade 4\b|(?:4th|fourth) grade|(?:9|nine)[-\s]?year[-\s]?old',
            "5": r'\bgrade 5\b|(?:5th|fifth) grade|(?:10|ten)[-\s]?year[-\s]?old',
            "6": r'\bgrade 6\b|(?:6th|sixth) grade|(?:11|eleven)[-\s]?year[-\s]?old',
            "7": r'\bgrade 7\b|(?:7th|seventh) grade|(?:12|twelve)[-\s]?year[-\s]?old',
            "8": r'\bgrade 8\b|(?:8th|eighth) grade|(?:13|thirteen)[-\s]?year[-\s]?old',
            "9": r'\bgrade 9\b|(?:9th|ninth) grade|(?:14|fourteen)[-\s]?year[-\s]?old|freshman',
            "10": r'\bgrade 10\b|(?:10th|tenth) grade|(?:15|fifteen)[-\s]?year[-\s]?old|sophomore',
            "11": r'\bgrade 11\b|(?:11th|eleventh) grade|(?:16|sixteen)[-\s]?year[-\s]?old|junior',
            "12": r'\bgrade 12\b|(?:12th|twelfth) grade|(?:17|seventeen)[-\s]?year[-\s]?old|senior'
        }
        
        # Get the grade_options map from the API 
        grade_options = self.eligibility_api.grade_options()
        
        # Check each pattern against the user input
        for grade, pattern in grade_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                # Save the human-readable grade for display
                grade_display_map = {
                    "K0": "Kindergarten 0 (K0)", 
                    "K1": "Kindergarten 1 (K1)",
                    "K2": "Kindergarten 2 (K2)"
                }
                self.conversation_state["grade_display"] = grade_display_map.get(grade, f"Grade {grade}")
                return grade_options.get(grade)
                
        # Default to K2 (kindergarten) if no grade is detected and we're not specifically asking
        if self.conversation_state["waiting_for"] != "grade":
            return grade_options.get("K2")
        return None
    
    def extract_language_info(self, user_input):
        """
        Extract language preference from user input.
        
        Args:
            user_input (str): The user's question or statement
            
        Returns:
            str: Language ID (defaults to English if not found)
        """
        # Define patterns for language detection
        language_mapping = {
            "English": r'\benglish\b',
            "Spanish": r'\bspanish\b|\bespañol\b',
            "Arabic": r'\barabic\b|\bعربي\b',
            "Mandarin": r'\bmandarin\b|\bchinese\b',
            "Burmese": r'\bburmese\b',
            "Cambodian": r'\bcambodian\b|\bkhmer\b',
            "Cantonese": r'\bcantonese\b',
            "Cape Verdean": r'\bcape verdean\b|\bcreole\b',
            "French": r'\bfrench\b|\bfrançais\b',
            "Greek": r'\bgreek\b',
            "Haitian Creole": r'\bhaitian\b|\bhaitian creole\b',
            "H'Mong": r"\bh[\'']?mong\b",
            "Italian": r'\bitalian\b|\bitaliano\b',
            "Korean": r'\bkorean\b',
            "Portuguese": r'\bportuguese\b|\bportuguês\b',
            "Russian": r'\brussian\b',
            "Somali": r'\bsomali\b',
            "Toishanese": r'\btoishanese\b',
            "Vietnamese": r'\bvietnamese\b'
        }
        
        # If we're explicitly waiting for a language, be more lenient
        if self.conversation_state["waiting_for"] == "language":
            # Check direct language responses with a simpler approach
            user_input_lower = user_input.lower()
            for language in language_mapping:
                if language.lower() in user_input_lower:
                    self.conversation_state["language_display"] = language
                    return self.eligibility_api.language_options().get(language)
        
        # Get language options from the API
        language_options = self.eligibility_api.language_options()
        
        # Check each language pattern against the user input
        for language, pattern in language_mapping.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                self.conversation_state["language_display"] = language
                return language_options.get(language)
        
        # Default to English if no language is detected and we're not specifically asking
        if self.conversation_state["waiting_for"] != "language":
            self.conversation_state["language_display"] = "English"
            return language_options.get("English")
        return None
    
    def is_asking_for_schools(self, user_input):
        """Check if the user is asking about eligible schools"""
        school_inquiry_pattern = r'what schools|eligible schools|available schools|school(?:s)? (?:for|near|in|around)|find (?:a )?school|where (?:can|should) (?:I|we) send|list of schools'
        return bool(re.search(school_inquiry_pattern, user_input, re.IGNORECASE))
    
    def determine_missing_info(self):
        """Determine what information is missing for school eligibility search"""
        missing = []
        if not self.conversation_state["address"]:
            missing.append("address")
        if not self.conversation_state["grade"]:
            missing.append("grade")
        if not self.conversation_state["language"]:
            missing.append("language")
        return missing
    
    def handle_follow_up_question(self, user_input):
        """
        Handle follow-up questions based on previous context.
        
        Args:
            user_input (str): The user's input
            
        Returns:
            str or None: Response if handled, None otherwise
        """
        # Check if we're waiting for specific information
        waiting_for = self.conversation_state["waiting_for"]
        
        if waiting_for == "address":
            address = self.extract_address_info(user_input)
            if address:
                self.conversation_state["address"] = address
                self.conversation_state["waiting_for"] = None
                
                # If we have all info needed for school search, proceed
                missing = self.determine_missing_info()
                if not missing:
                    return self.search_eligible_schools()
                else:
                    # Ask for the next piece of info
                    next_missing = missing[0]
                    self.conversation_state["waiting_for"] = next_missing
                    if next_missing == "grade":
                        return "Thank you for providing your address. What grade will your child be entering?"
                    elif next_missing == "language":
                        return "Thank you for providing your address. What is your preferred language?"
            else:
                return "I'm having trouble understanding your address. Please provide a Boston address with zip code, like '123 Main St, Boston, MA 02115'."
        
        elif waiting_for == "grade":
            grade_id = self.extract_grade_info(user_input)
            if grade_id:
                self.conversation_state["grade"] = grade_id
                self.conversation_state["waiting_for"] = None
                
                # If we have all info needed for school search, proceed
                missing = self.determine_missing_info()
                if not missing:
                    return self.search_eligible_schools()
                else:
                    # Ask for the next piece of info
                    next_missing = missing[0]
                    self.conversation_state["waiting_for"] = next_missing
                    if next_missing == "address":
                        return f"Thank you for letting me know your child will be in {self.conversation_state.get('grade_display', 'that grade')}. What is your address or zip code in Boston?"
                    elif next_missing == "language":
                        return f"Thank you for letting me know your child will be in {self.conversation_state.get('grade_display', 'that grade')}. What is your preferred language?"
            else:
                return "I'm not sure I understood the grade level. Please specify if your child will be in K0 (3 years old), K1 (4 years old), K2 (kindergarten/5 years old), or grades 1-12."
        
        elif waiting_for == "language":
            language_id = self.extract_language_info(user_input)
            if language_id:
                self.conversation_state["language"] = language_id
                self.conversation_state["waiting_for"] = None
                
                # If we have all info needed for school search, proceed
                missing = self.determine_missing_info()
                if not missing:
                    return self.search_eligible_schools()
                else:
                    # Ask for the next piece of info
                    next_missing = missing[0]
                    self.conversation_state["waiting_for"] = next_missing
                    if next_missing == "address":
                        return f"Thank you for selecting {self.conversation_state.get('language_display', 'your language')}. What is your address or zip code in Boston?"
                    elif next_missing == "grade":
                        return f"Thank you for selecting {self.conversation_state.get('language_display', 'your language')}. What grade will your child be entering?"
            else:
                return "I didn't recognize that language. Please choose from options like English, Spanish, Mandarin, etc."
            
        # Check if it's a follow-up about previously found schools
        if self.conversation_state["last_school_results"] and re.search(r'tell me more about|more information|details (about|on)|what about|where is', user_input, re.IGNORECASE):
            # Try to identify which school they're asking about
            schools = self.conversation_state["last_school_results"]
            
            # Check for school number references (e.g., "Tell me more about #3")
            number_match = re.search(r'#?(\d+)', user_input)
            if number_match and schools:
                try:
                    index = int(number_match.group(1)) - 1
                    if 0 <= index < len(schools):
                        school = schools[index]
                        return f"Here's more information about {school.get('name', 'the school')}:\n\nAddress: {school.get('address', 'Information not available')}\nReferenceID: {school.get('referenceId', 'N/A')}\n\nFor complete details and registration information, please visit https://boston.explore.avela.org/ or contact a BPS Welcome Center at 617-635-9010."
                except:
                    pass
                    
            # Check for school name mentions
            for idx, school in enumerate(schools):
                school_name = school.get('name', '').lower()
                if school_name and school_name in user_input.lower():
                    return f"Here's more information about {school.get('name', 'the school')}:\n\nAddress: {school.get('address', 'Information not available')}\nReferenceID: {school.get('referenceId', 'N/A')}\n\nFor complete details and registration information, please visit https://boston.explore.avela.org/ or contact a BPS Welcome Center at 617-635-9010."
        
        return None
    
    def search_eligible_schools(self):
        """Search for eligible schools using the information we have"""
        try:
            # First ensure we have all needed information
            if not all([self.conversation_state["address"], self.conversation_state["grade"], self.conversation_state["language"]]):
                missing = self.determine_missing_info()
                return f"To find eligible schools, I still need your {', '.join(missing)}."
            
            # Call the API to find eligible schools
            results = self.eligibility_api.find_eligible_schools(
                grade_id=self.conversation_state["grade"],
                address=self.conversation_state["address"],
                language_id=self.conversation_state["language"]
            )
            
            # Process results
            eligible_schools = results.get("schools", [])
            self.conversation_state["last_school_results"] = eligible_schools
            
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
                    
                schools_info += "For more details, please visit: https://boston.explore.avela.org/\n\nYou can ask me for more information about any specific school by name or number (e.g., 'Tell me more about #3')."
                return schools_info
            else:
                return "I couldn't find any eligible schools for your location and student information. Please verify your address is in Boston and try again, or visit https://boston.explore.avela.org/ directly."
        except Exception as e:
            print(f"API error: {e}")
            return f"I apologize, but I encountered an error searching for schools: {str(e)}"
    
    def get_response(self, user_input, history=None):
        """
        Generate responses to user questions about Boston schools, with conversation state management.
        
        Args:
            user_input (str): The user's question about Boston schools
            history (list, optional): Previous conversation history as [user_msg, assistant_msg] pairs

        Returns:
            str: The chatbot's response

        Implementation tips:
        - Use self.format_prompt() to format the user's input
        - Use self.client to generate responses
        """
        # Process direct responses to questions we've asked
        follow_up_response = self.handle_follow_up_question(user_input)
        if follow_up_response:
            return follow_up_response
        
        # Extract information from the user input to build our context
        address = self.extract_address_info(user_input)
        if address:
            self.conversation_state["address"] = address
            
        grade_id = self.extract_grade_info(user_input)
        if grade_id:
            self.conversation_state["grade"] = grade_id
            
        language_id = self.extract_language_info(user_input)
        if language_id:
            self.conversation_state["language"] = language_id
        
        # Check if user is asking about eligible schools
        if self.is_asking_for_schools(user_input):
            # Determine if we're missing any info needed for search
            missing = self.determine_missing_info()
            
            if not missing:
                # We have all the info we need, proceed with search
                return self.search_eligible_schools()
            else:
                # Ask for the first missing piece of information
                first_missing = missing[0]
                self.conversation_state["waiting_for"] = first_missing
                
                if first_missing == "address":
                    return "To help you find eligible schools, I need your address or zip code in Boston. What is your address?"
                elif first_missing == "grade":
                    return "To find schools that match your needs, I need to know what grade your child will be entering. Is your child in kindergarten (K0, K1, K2) or grades 1-12?"
                elif first_missing == "language":
                    return "To find the right schools, I need to know your language preference. What language would you prefer?"
        
        # Check if response is asking to reset or start over
        if re.search(r'start over|reset|clear|new search|different (address|location|grade|child)', user_input, re.IGNORECASE):
            self.reset_state()
            return "I've reset our conversation. How can I help you with Boston Public Schools today?"
        
        # Default behavior: use the model
        prompt = self.format_prompt(user_input, history)
        
        try:
            print("Generating response...")
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


