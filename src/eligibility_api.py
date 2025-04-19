"""
Boston Schools Eligibility API Module

This module provides functions to interact with the Avela API for finding eligible schools
in Boston based on student details and address information.
"""

import requests
from typing import Dict, Any, Optional, List

class EligibilityAPI:
    """
    Client for the Boston Schools Eligibility API.
    """
    
    BASE_URL = "https://prod.execute-api.apply.avela.org/eligibility/organizations/boston/formTemplates/2f58f4ce-b462-4028-ae59-7ab874fc1224/findEligibility"
    
    # Static list of all Boston schools - this would ideally come from a separate API call or database
    ALL_SCHOOLS = [
        {"id": "4532d8a9-7ef3-4a90-aa4f-3c5149560474", "name": "Madison Park Technical Vocational High School", "referenceId": "1210"},
        {"id": "71e955b2-36ea-4e34-848e-63a78ed0688e", "name": "Mission Grammar School", "referenceId": "259028"},
        {"id": "7d0ac7b2-c79a-4614-a614-c858e517e1b8", "name": "Murphy K-8 School", "referenceId": "4400"},
        {"id": "a35500f2-89da-4e4b-b088-8646cfd2fd5b", "name": "YMCA - Roxbury Tenants of Harvard (RTH)", "referenceId": "187660"},
        {"id": "4b084cc6-88e7-4417-8c67-dbb4a9cfaea0", "name": "Fenway High School", "referenceId": "1265"},
        {"id": "6ded6119-1572-4941-8c98-d2a19c48f390", "name": "Little Amigos Early Learning Center", "referenceId": "260040"},
        {"id": "779dc3b2-8056-4c81-b1bd-d507336435e3", "name": "O'Donnell Elementary School", "referenceId": "4543"},
        {"id": "6a3a0f1d-3861-434c-a084-b2b1a8334868", "name": "Bridge to Nature", "referenceId": "187594"},
        # Add more schools as they become known
        {"id": "school-1", "name": "Boston Arts Academy", "referenceId": "1001"},
        {"id": "school-2", "name": "Boston Latin School", "referenceId": "1002"},
        {"id": "school-3", "name": "Boston Latin Academy", "referenceId": "1003"},
        {"id": "school-4", "name": "John D. O'Bryant School", "referenceId": "1004"},
        {"id": "school-5", "name": "Josiah Quincy School", "referenceId": "1005"}
    ]
    
    def __init__(self):
        """Initialize the API client with default headers."""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://boston.explore.avela.org",
            "Referer": "https://boston.explore.avela.org/"
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
        # Extract ineligible school IDs from the API response
        ineligible_school_ids = []
        if "ineligibleSchools" in api_response:
            ineligible_school_ids = [school["id"] for school in api_response["ineligibleSchools"]]
        
        # If API returns complete school list, use that instead of our static list
        all_schools = api_response.get("allSchools", self.ALL_SCHOOLS)
        
        # Filter out ineligible schools to get eligible ones
        eligible_schools = [
            school for school in all_schools 
            if school["id"] not in ineligible_school_ids
        ]
        
        # If we're working with the static list, we need to add addresses
        # In a real implementation, this would come from the API
        for school in eligible_schools:
            if "address" not in school:
                school["address"] = f"Boston, MA"
        
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
    
    @staticmethod
    def grade_options() -> Dict[str, str]:
        """
        Returns mapping of grade names to their API IDs.
        
        Returns:
            Dict[str, str]: Dictionary mapping grade names to their IDs
        """
        return {
            "K0": "a409dc76-94cc-471c-bc68-c7b68d05147d",
            "K1": "4c198e2d-50cc-4b61-9528-4c7e4a800a91",
            "K2": "8a08963a-4683-410c-8eef-52c1a81c2c02",
            # Add other grades as needed
        }
    
    @staticmethod
    def language_options() -> Dict[str, str]:
        """
        Returns mapping of language names to their API IDs.
        
        Returns:
            Dict[str, str]: Dictionary mapping language names to their IDs
        """
        return {
            "English": "01614035-4bc6-404f-adef-c72643b8bd3d",
            "Spanish": "cfdef96c-58fa-4ce0-a44d-fd328ac520a6",
            # Add other languages as needed
        } 