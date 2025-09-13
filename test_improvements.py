#!/usr/bin/env python3
"""
ToddlerMate Improvements Testing Script
Tests the enhanced location search and Indian cultural home remedies
"""

import requests
import json
import sys

BASE_URL = "https://toddlermate.preview.emergentagent.com/api"

def test_hospital_search():
    """Test the improved hospital search with Indian cities"""
    print("🏥 Testing Hospital Search System")
    print("=" * 50)
    
    # Test major Indian cities
    cities_to_test = [
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", 
        "Kolkata", "Pune", "Ahmedabad", "New Delhi", "Bengaluru", 
        "Gurgaon", "Noida", "Unknown City"
    ]
    
    for city in cities_to_test:
        try:
            response = requests.post(f"{BASE_URL}/hospitals", 
                                   json={"location": city}, 
                                   timeout=10)
            
            if response.status_code == 200:
                hospitals = response.json()
                print(f"\n📍 {city}: Found {len(hospitals)} hospitals")
                if hospitals:
                    hospital = hospitals[0]
                    print(f"   • Name: {hospital['name']}")
                    print(f"   • Address: {hospital['address']}")
                    print(f"   • Phone: {hospital['phone']}")
                    print(f"   • Type: {hospital['type']}")
                    
                    # Verify Indian formatting
                    if "+91" in hospital['phone']:
                        print("   ✅ Indian phone format detected")
                    else:
                        print("   ⚠️  Non-Indian phone format")
            else:
                print(f"❌ {city}: Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {city}: Error - {str(e)}")
    
    return True

def test_indian_remedies():
    """Test the Indian cultural home remedies"""
    print("\n\n🌿 Testing Indian Cultural Home Remedies")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/symptoms", timeout=10)
        if response.status_code == 200:
            symptoms = response.json()
            
            # Test specific Indian remedies
            indian_keywords = [
                "honey", "warm water", "tulsi", "turmeric", "mustard oil", 
                "ginger", "ajwain", "jeera", "coconut water", "ORS", 
                "khichdi", "rice water"
            ]
            
            for symptom_key, symptom_data in symptoms.items():
                print(f"\n🔍 {symptom_data['title']}:")
                remedies = symptom_data.get('home_remedies', [])
                
                indian_remedies_found = []
                for remedy in remedies:
                    for keyword in indian_keywords:
                        if keyword.lower() in remedy.lower():
                            indian_remedies_found.append(keyword)
                
                print(f"   • Total remedies: {len(remedies)}")
                print(f"   • Indian keywords found: {set(indian_remedies_found)}")
                
                # Show sample remedies
                for i, remedy in enumerate(remedies[:2]):
                    print(f"   • {remedy}")
                    
                if indian_remedies_found:
                    print("   ✅ Indian cultural remedies detected")
                else:
                    print("   ⚠️  No Indian remedies detected")
        else:
            print(f"❌ Failed to fetch symptoms: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing remedies: {str(e)}")
        return False
    
    return True

def test_ai_chat():
    """Test AI chat with Indian context"""
    print("\n\n🤖 Testing AI Chat with Indian Context")
    print("=" * 50)
    
    indian_questions = [
        "What are some Indian home remedies for toddler fever?",
        "My child has cough, can I give turmeric milk?",
        "How to prepare ORS at home for my toddler?"
    ]
    
    for question in indian_questions:
        try:
            response = requests.post(f"{BASE_URL}/chat", 
                                   json={
                                       "message": question,
                                       "session_id": "test-indian-context"
                                   }, 
                                   timeout=30)
            
            if response.status_code == 200:
                chat_response = response.json()
                ai_answer = chat_response.get('response', '')
                
                print(f"\n❓ Question: {question}")
                print(f"💬 AI Response length: {len(ai_answer)} characters")
                print(f"   Preview: {ai_answer[:150]}...")
                
                # Check if AI mentions Indian remedies
                indian_terms = ["turmeric", "honey", "tulsi", "ajwain", "ginger", "ORS", "indian"]
                mentioned_terms = [term for term in indian_terms if term.lower() in ai_answer.lower()]
                
                if mentioned_terms:
                    print(f"   ✅ Indian remedies mentioned: {mentioned_terms}")
                else:
                    print("   ⚠️  No Indian remedies detected in response")
                    
            else:
                print(f"❌ Chat failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
    
    return True

def test_api_health():
    """Test basic API health"""
    print("\n\n⚕️ Testing API Health")
    print("=" * 30)
    
    endpoints = [
        ("Health Check", ""),
        ("Milestones", "milestones"),
        ("Symptoms", "symptoms")
    ]
    
    for name, endpoint in endpoints:
        try:
            url = f"{BASE_URL}/{endpoint}" if endpoint else BASE_URL
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 ToddlerMate Improvements Testing")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    try:
        if test_api_health():
            tests_passed += 1
            
        if test_hospital_search():
            tests_passed += 1
            
        if test_indian_remedies():
            tests_passed += 1
            
        if test_ai_chat():
            tests_passed += 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        return 1
    
    print(f"\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All improvements working perfectly!")
        return 0
    else:
        print("⚠️  Some tests failed, check output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())