import requests
import sys
import json
from datetime import datetime

class ToddlerMateAPITester:
    def __init__(self, base_url="https://toddlermate.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response preview: {str(response_data)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_get_milestones(self):
        """Test getting development milestones"""
        success, response = self.run_test(
            "Get Development Milestones",
            "GET",
            "milestones",
            200
        )
        
        if success:
            # Validate response structure
            expected_keys = ["0-6_months", "6-12_months", "1-2_years", "2-3_years"]
            for key in expected_keys:
                if key not in response:
                    print(f"❌ Missing milestone category: {key}")
                    return False
                if "title" not in response[key] or "milestones" not in response[key]:
                    print(f"❌ Invalid structure for {key}")
                    return False
            print("✅ Milestone data structure is valid")
        
        return success

    def test_get_symptoms(self):
        """Test getting health symptoms with Indian cultural remedies"""
        success, response = self.run_test(
            "Get Health Symptoms",
            "GET",
            "symptoms",
            200
        )
        
        if success:
            # Validate response structure
            expected_keys = ["fever", "cough", "stomach", "sleep"]
            for key in expected_keys:
                if key not in response:
                    print(f"❌ Missing symptom category: {key}")
                    return False
                required_fields = ["title", "description", "home_remedies", "when_to_see_doctor"]
                for field in required_fields:
                    if field not in response[key]:
                        print(f"❌ Missing field {field} in {key}")
                        return False
            
            # Test Indian cultural remedies
            print("\n🔍 Checking Indian Cultural Remedies...")
            
            # Fever remedies
            fever_remedies = response["fever"]["home_remedies"]
            fever_indian_terms = ["honey", "tulsi", "mustard oil"]
            fever_found = [term for term in fever_indian_terms if any(term.lower() in remedy.lower() for remedy in fever_remedies)]
            print(f"   Fever - Found Indian remedies: {fever_found}")
            
            # Cough remedies  
            cough_remedies = response["cough"]["home_remedies"]
            cough_indian_terms = ["ginger", "honey", "turmeric", "ajwain"]
            cough_found = [term for term in cough_indian_terms if any(term.lower() in remedy.lower() for remedy in cough_remedies)]
            print(f"   Cough - Found Indian remedies: {cough_found}")
            
            # Stomach remedies
            stomach_remedies = response["stomach"]["home_remedies"]
            stomach_indian_terms = ["ORS", "jeera", "khichdi", "rice water"]
            stomach_found = [term for term in stomach_indian_terms if any(term.lower() in remedy.lower() for remedy in stomach_remedies)]
            print(f"   Stomach - Found Indian remedies: {stomach_found}")
            
            # Sleep remedies
            sleep_remedies = response["sleep"]["home_remedies"]
            sleep_indian_terms = ["oil massage", "turmeric", "head massage"]
            sleep_found = [term for term in sleep_indian_terms if any(term.lower() in remedy.lower() for remedy in sleep_remedies)]
            print(f"   Sleep - Found Indian remedies: {sleep_found}")
            
            # Check if we found enough Indian cultural elements
            total_found = len(fever_found) + len(cough_found) + len(stomach_found) + len(sleep_found)
            if total_found >= 8:  # Should find most of the expected terms
                print("✅ Indian cultural remedies are well represented")
            else:
                print(f"⚠️  Only found {total_found} Indian cultural remedy terms")
            
            print("✅ Symptoms data structure is valid")
        
        return success

    def test_hospital_search(self):
        """Test hospital search functionality with Indian cities"""
        # Test main Indian cities
        main_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune", "Ahmedabad"]
        
        # Test city variations
        city_variations = ["New Delhi", "Navi Mumbai", "Bengaluru", "Gurgaon", "Noida"]
        
        # Test unknown cities
        unknown_cities = ["UnknownCity", "RandomPlace"]
        
        all_test_locations = main_cities + city_variations + unknown_cities
        
        for location in all_test_locations:
            success, response = self.run_test(
                f"Hospital Search - {location}",
                "POST",
                "hospitals",
                200,
                data={"location": location}
            )
            
            if success:
                if isinstance(response, list) and len(response) > 0:
                    # Validate hospital structure
                    hospital = response[0]
                    required_fields = ["id", "name", "address", "type"]
                    for field in required_fields:
                        if field not in hospital:
                            print(f"❌ Missing field {field} in hospital data")
                            return False
                    
                    # Check for Indian address formatting and phone numbers
                    if location in main_cities or location in city_variations:
                        # Should have proper Indian addresses
                        address = hospital.get("address", "")
                        phone = hospital.get("phone", "")
                        
                        # Check if address contains Indian state/city info
                        indian_indicators = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana", "West Bengal", "Gujarat", "Uttar Pradesh"]
                        has_indian_address = any(indicator in address for indicator in indian_indicators)
                        
                        if has_indian_address:
                            print(f"✅ Found proper Indian address: {address[:50]}...")
                        else:
                            print(f"⚠️  Address may not be Indian format: {address}")
                        
                        # Check phone number format (+91)
                        if phone and "+91" in phone:
                            print(f"✅ Found Indian phone format: {phone}")
                        elif phone:
                            print(f"⚠️  Phone number may not be Indian format: {phone}")
                    
                    print(f"✅ Hospital search returned {len(response)} hospitals for {location}")
                else:
                    if location in unknown_cities:
                        print(f"✅ Fallback behavior working for unknown city: {location}")
                    else:
                        print(f"❌ No hospitals returned for known city: {location}")
                        return False
            else:
                return False
        
        return True

    def test_ai_chat(self):
        """Test AI chat functionality"""
        test_messages = [
            "What are normal sleep patterns for a 2-year-old?",
            "My toddler has a fever of 101°F. What should I do?",
            "When should my 18-month-old start walking?"
        ]
        
        for message in test_messages:
            success, response = self.run_test(
                f"AI Chat - '{message[:30]}...'",
                "POST",
                "chat",
                200,
                data={
                    "message": message,
                    "session_id": self.session_id
                },
                timeout=60  # AI responses may take longer
            )
            
            if success:
                if "response" in response and "session_id" in response:
                    if not self.session_id:
                        self.session_id = response["session_id"]
                        print(f"   Session ID: {self.session_id}")
                    
                    ai_response = response["response"]
                    if len(ai_response) > 10:  # Basic validation
                        print(f"✅ AI responded with {len(ai_response)} characters")
                        print(f"   AI Response preview: {ai_response[:100]}...")
                    else:
                        print(f"❌ AI response too short: {ai_response}")
                        return False
                else:
                    print(f"❌ Invalid chat response structure")
                    return False
            else:
                return False
        
        return True

    def test_invalid_endpoints(self):
        """Test error handling for invalid endpoints"""
        # Test invalid hospital search (missing location)
        success, response = self.run_test(
            "Invalid Hospital Search (no location)",
            "POST",
            "hospitals",
            422,  # Validation error expected
            data={}
        )
        
        # Test invalid chat (empty message)
        success2, response2 = self.run_test(
            "Invalid Chat (empty message)",
            "POST",
            "chat",
            422,  # Validation error expected
            data={"message": ""}
        )
        
        return success or success2  # At least one should handle errors properly

def main():
    print("🚀 Starting ToddlerMate API Testing...")
    print("=" * 60)
    
    # Setup
    tester = ToddlerMateAPITester()
    
    # Run all tests
    tests = [
        ("API Health Check", tester.test_health_check),
        ("Development Milestones", tester.test_get_milestones),
        ("Health Symptoms", tester.test_get_symptoms),
        ("Hospital Search", tester.test_hospital_search),
        ("AI Chat", tester.test_ai_chat),
        ("Error Handling", tester.test_invalid_endpoints)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if failed_tests:
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print(f"\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())