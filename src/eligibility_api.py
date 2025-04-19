"""
Boston Schools Eligibility API Module

This module provides functions to interact with the Avela API for finding eligible schools
in Boston based on student details and address information.
"""

import requests
import json
from typing import Dict, Any, Optional, List
import os

class EligibilityAPI:
    """
    Client for the Boston Schools Eligibility API.
    """
    
    BASE_URL = "https://prod.execute-api.apply.avela.org/eligibility/organizations/boston/formTemplates/2f58f4ce-b462-4028-ae59-7ab874fc1224/findEligibility"
    
    # Load the complete list of schools from the minified JSON file
    def __init__(self):
        """Initialize the API client with default headers and load school data."""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://boston.explore.avela.org",
            "Referer": "https://boston.explore.avela.org/"
        }
        
        # Load the schools data from the minified JSON file
        try:
            with open("all_schools_minified.json", "r", encoding="utf-8") as f:
                schools_data = json.load(f)
                self.ALL_SCHOOLS = []
                for school in schools_data:
                    self.ALL_SCHOOLS.append({
                        "id": school.get("id", ""),
                        "name": school.get("name", ""),
                        "referenceId": school.get("id", ""), # Use the id as referenceId
                        "address": school.get("address", "")
                    })
        except Exception as e:
            print(f"Error loading schools data: {e}")
    
    # Grade to UUID mapping
    GRADE_TO_UUID = {
        "Grade K0 (3 years old)": "a409dc76-94cc-471c-bc68-c7b68d05147d",
        "Grade K1 (4 years old)": "9e1e0cbf-c147-48ac-a961-34fc97a0be67",
        "Grade K2 (5 years old)": "4134373f-5e12-4a03-b36f-c0a545db9eb7",
        "1": "eaf903c1-b6c5-4c9d-8905-dc6152ac9f5e",
        "2": "fb580408-4db9-4e54-8191-cdd6bd95a4fe",
        "3": "f59adf0b-69d4-4b5b-8a40-5e87886eaba7",
        "4": "bd63e458-16cc-46ed-a260-c936a85fdc55",
        "5": "12746de8-ab87-4af5-b8ef-abcb83285467",
        "6": "bb81c16d-2f72-41a9-929c-9316f2143780",
        "7": "92efe874-5e03-4037-aefd-1edded298e46",
        "8": "f2529c1b-c1c1-4fb6-bf2d-c2de261d3b5b",
        "9": "f6b26370-247e-4ef3-8144-0b1eddc86849",
        "10": "d98e3523-82c7-4940-9177-a4d92807914f",
        "11": "5d40fd74-63bd-49ce-8439-8b3a55ed0864",
        "12": "2ce44985-23b2-438a-906e-e56369300467"
    }
    
    # Language to UUID mapping
    LANGUAGE_TO_UUID = {
        "English": "01614035-4bc6-404f-adef-f35ef2d39192",
        "Spanish": "8ec25e1f-4b80-4870-a241-e5a5268bf406",
        "Arabic": "db23f5cc-c0fa-4fe4-872d-73dc6d2bff84",
        "Mandarin": "f1ef8da1-7cac-45ab-8eb8-95bef0fb6b58",
        "Burmese": "b8ab12cd-6c8d-4d30-926b-b47f0db22a45",
        "Cambodian": "c3900f20-233a-48f2-9883-c15b4777197b",
        "Cantonese": "9f66a115-e9f3-483a-b571-704a7ef220eb",
        "Cape Verdean": "41fdcd94-a1cd-4f76-bb5b-fa4232a9d036",
        "French": "3a266ac4-08c1-4978-8e7f-a9eff51483d8",
        "Greek": "f1ff0ead-25af-4dce-b805-b3c2bccfc8ea",
        "Haitian Creole": "0f6ee3c9-792d-4d0c-b6c2-6db3759ddaf9",
        "H'Mong": "c3e5706a-4600-4867-a531-43b14b648d9a",
        "Italian": "e65ba112-51d5-4b08-8e1c-924dfb831760",
        "Korean": "576debcd-872b-40aa-80a8-087832a0af59",
        "Portuguese": "f0e7b707-1beb-4a27-b0cb-4a74a57f1b0f",
        "Russian": "d8701bba-106e-4063-8bf5-f0836699c673",
        "Somali": "47e4c94d-3dc0-4aeb-8929-20567971e3e3",
        "Toishanese": "814d20d0-bc06-46f0-84af-c0bd4abdfa21",
        "Vietnamese": "fbf50558-6cdb-46c4-b079-5a8498fba82a",
        "Other": "64351764-04ed-4828-8320-35579deca69b"
    }
    
    def find_eligible_schools(self, 
                             grade_id: str,
                             address: Dict[str, str],
                             language_id: str) -> Dict[str, Any]:
        """
        Find eligible schools based on student details.
        
        Args:
            grade_id (str): ID of the student's grade level
            address (Dict[str, str]): Dictionary containing address components 
                with keys: streetAddress, streetAddressLine2, city, state, zipCode
            language_id (str): ID of the student's primary language
            
        Returns:
            Dict[str, Any]: A dictionary containing eligible schools based on filtering
            
        Raises:
            Exception: If the API request fails
        """
        payload = {
            "applicationType": "Explore",
            "questionIdToAnswer": {
                "33c5f494-eafb-4abd-92a3-8d508afae7e6": grade_id,
                "b7d642af-5bf7-4ac5-ae56-e4d5704c4cb0": address,
                "823a2ee3-02c9-4d8c-85fd-f35ef2d39192": language_id
            }
        }
        
        response = requests.post(self.BASE_URL, headers=self.headers, json=payload)
        
        if response.ok:
            api_response = response.json()
            # Get the eligible schools by filtering out ineligible ones
            eligible_schools = self.get_eligible_schools(api_response)
            return {"schools": eligible_schools, "raw_response": api_response}
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    def get_eligible_schools(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract eligible schools by comparing all schools with ineligible schools.
        
        Args:
            api_response (Dict[str, Any]): The raw API response
            
        Returns:
            List[Dict[str, Any]]: List of eligible schools
        """
        # Extract ineligible school reference_ids from the API response
        ineligible_school_ids = []
        if "ineligibleSchools" in api_response:
            ineligible_school_ids = [school["referenceId"] for school in api_response["ineligibleSchools"]]
        
        all_schools = json.load(open("all_schools_minified.json"))

        # Filter out ineligible schools to get eligible ones
        eligible_schools = [
            school for school in all_schools 
            if school["id"] not in ineligible_school_ids
        ]
        
        return eligible_schools
    
    def get_school_details(self, school_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific school.
        
        Args:
            school_id (str): The ID of the school to get details for
            
        Returns:
            Dict[str, Any]: School details
            
        Note: 
            This is a placeholder method. The actual implementation would depend on 
            the API endpoint for school details which isn't provided in the initial code.
        """
        # Placeholder for future implementation
        pass
        
    def get_full_school_details(self, school_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a specific school from en.data.json
        
        Args:
            school_id (str): The ID of the school to get details for
            
        Returns:
            Dict[str, Any]: Detailed school information or empty dict if not found
        """
        try:
            # Load the full school data from en.data.json
            # The file seems to have some formatting issues, so we need to handle it carefully
            with open("en.data.json", "r", encoding="utf-8") as f:
                # Read and fix json format
                data = f.read()
                data = data.replace("%", "")  # Remove any trailing % characters
                # Try loading as JSON
                try:
                    schools_data = json.loads(data)
                except json.JSONDecodeError:
                    # If the file doesn't parse correctly, it may need additional cleaning
                    print("Error parsing en.data.json - attempting alternative parsing")
                    # Try to extract schools as a list from the file content
                    if data.startswith("[{") and data.endswith("}]"):
                        # Remove any trailing characters after the last closing bracket
                        clean_data = data[:data.rindex("}]") + 2]
                        try:
                            schools_data = json.loads(clean_data)
                        except:
                            print("Failed to parse en.data.json even after cleaning")
                            return {}
                    else:
                        print("Cannot identify JSON structure in en.data.json")
                        return {}
                
            # Find the school by ID - strictly compare strings to avoid type issues
            for school in schools_data:
                if str(school.get("id", "")) == str(school_id):
                    return school
                    
        except Exception as e:
            print(f"Error loading full school data: {e}")
            return {}
    
    @staticmethod
    def grade_options() -> Dict[str, str]:
        """
        Returns mapping of grade names to their API IDs.
        
        Returns:
            Dict[str, str]: Dictionary mapping grade names to their IDs
        """
        return {
            "K0": "a409dc76-94cc-471c-bc68-c7b68d05147d",
            "K1": "9e1e0cbf-c147-48ac-a961-34fc97a0be67",
            "K2": "4134373f-5e12-4a03-b36f-c0a545db9eb7",
            "1": "eaf903c1-b6c5-4c9d-8905-dc6152ac9f5e",
            "2": "fb580408-4db9-4e54-8191-cdd6bd95a4fe",
            "3": "f59adf0b-69d4-4b5b-8a40-5e87886eaba7",
            "4": "bd63e458-16cc-46ed-a260-c936a85fdc55",
            "5": "12746de8-ab87-4af5-b8ef-abcb83285467",
            "6": "bb81c16d-2f72-41a9-929c-9316f2143780", 
            "7": "92efe874-5e03-4037-aefd-1edded298e46",
            "8": "f2529c1b-c1c1-4fb6-bf2d-c2de261d3b5b",
            "9": "f6b26370-247e-4ef3-8144-0b1eddc86849",
            "10": "d98e3523-82c7-4940-9177-a4d92807914f",
            "11": "5d40fd74-63bd-49ce-8439-8b3a55ed0864",
            "12": "2ce44985-23b2-438a-906e-e56369300467"
        }
    
    @staticmethod
    def language_options() -> Dict[str, str]:
        """
        Returns mapping of language names to their API IDs.
        
        Returns:
            Dict[str, str]: Dictionary mapping language names to their IDs
        """
        return {
            "English": "01614035-4bc6-404f-adef-f35ef2d39192",
            "Spanish": "8ec25e1f-4b80-4870-a241-e5a5268bf406",
            "Arabic": "db23f5cc-c0fa-4fe4-872d-73dc6d2bff84",
            "Mandarin": "f1ef8da1-7cac-45ab-8eb8-95bef0fb6b58",
            "Burmese": "b8ab12cd-6c8d-4d30-926b-b47f0db22a45",
            "Cambodian": "c3900f20-233a-48f2-9883-c15b4777197b",
            "Cantonese": "9f66a115-e9f3-483a-b571-704a7ef220eb",
            "Cape Verdean": "41fdcd94-a1cd-4f76-bb5b-fa4232a9d036",
            "French": "3a266ac4-08c1-4978-8e7f-a9eff51483d8",
            "Greek": "f1ff0ead-25af-4dce-b805-b3c2bccfc8ea",
            "Haitian Creole": "0f6ee3c9-792d-4d0c-b6c2-6db3759ddaf9",
            "H'Mong": "c3e5706a-4600-4867-a531-43b14b648d9a",
            "Italian": "e65ba112-51d5-4b08-8e1c-924dfb831760",
            "Korean": "576debcd-872b-40aa-80a8-087832a0af59",
            "Portuguese": "f0e7b707-1beb-4a27-b0cb-4a74a57f1b0f",
            "Russian": "d8701bba-106e-4063-8bf5-f0836699c673",
            "Somali": "47e4c94d-3dc0-4aeb-8929-20567971e3e3",
            "Toishanese": "814d20d0-bc06-46f0-84af-c0bd4abdfa21",
            "Vietnamese": "fbf50558-6cdb-46c4-b079-5a8498fba82a",
            "Other": "64351764-04ed-4828-8320-35579deca69b"
        } 