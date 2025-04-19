#!/usr/bin/env python3
"""
Test script for the Boston Schools Eligibility API.

Usage:
    python test_eligibility_api.py

This script demonstrates how to use the EligibilityAPI to find eligible schools
based on a sample address and student details.
"""

from src.eligibility_api import EligibilityAPI

def main():
    """Test the EligibilityAPI with sample data."""
    print("Testing Boston Schools Eligibility API...")
    
    # Create API client
    api = EligibilityAPI()
    
    # Sample data
    sample_address = {
        "streetAddress": "374 Commonwealth Ave",
        "streetAddressLine2": "",
        "city": "Boston",
        "state": "MA",
        "zipCode": "02115"
    }
    
    # Get grade ID for grade 3 (8-year-old)
    grade_options = api.grade_options()
    grade_id = grade_options.get("3")
    print(f"Using grade ID: {grade_id} for Grade 3")
    
    # Get language ID for Mandarin
    language_options = api.language_options()
    language_id = language_options.get("Mandarin")
    print(f"Using language ID: {language_id} for Mandarin")
    
    # Test API call
    try:
        print(f"Searching for schools near {sample_address['streetAddress']}, {sample_address['city']}...")
        results = api.find_eligible_schools(
            grade_id=grade_id,
            address=sample_address,
            language_id=language_id
        )
        
        # Print results
        eligible_schools = results.get("schools", [])
        raw_response = results.get("raw_response", {})
        
        if eligible_schools:
            print(f"\nFound {len(eligible_schools)} eligible schools:")
            for i, school in enumerate(eligible_schools[:10], 1):  # Limit to first 10 schools
                print(f"\n{i}. {school.get('name', 'Unknown School')}")
                if school.get('address'):
                    print(f"   Address: {school.get('address')}")
        else:
            print("No eligible schools found.")
        
        # Show raw response for debugging
        print("\nRaw API Response:")
        ineligible_count = len(raw_response.get("ineligibleSchools", []))
        print(f"API returned {ineligible_count} ineligible schools.")
            
    except Exception as e:
        print(f"Error occurred: {e}")
    
if __name__ == "__main__":
    main() 