"""
API Testing Script for Disaster Response Environment
Run this to verify all endpoints are working
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    print("1. Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.json()}")
    return response.status_code == 200

def test_tasks():
    print("\n2. Testing Tasks Endpoint...")
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()
    print(f"   Found {len(tasks['tasks'])} tasks")
    for task in tasks['tasks']:
        print(f"     - {task['id']}: {task['description'][:50]}...")
    return response.status_code == 200

def test_reset():
    print("\n3. Testing Reset Endpoint...")
    response = requests.post(f"{BASE_URL}/reset?difficulty=easy")
    data = response.json()
    print(f"   Session ID: {data['session_id'][:16]}...")
    print(f"   Scenario: {data['observation']['scenario_name']}")
    return data['session_id']

def test_step(session_id):
    print("\n4. Testing Step Endpoint...")
    
    # Create a sample action
    action = {
        "allocations": [
            {
                "resource_id": "resource_ambulance_0",
                "victim_id": "victim_0000",
                "priority": 8
            }
        ],
        "strategic": None,
        "confidence": 0.85
    }
    
    response = requests.post(
        f"{BASE_URL}/step?session_id={session_id}",
        json=action
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Observation received")
        print(f"   Time elapsed: {data['observation']['time_elapsed_hours']:.1f} hours")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_grader(session_id):
    print("\n5. Testing Grader Endpoint...")
    response = requests.post(f"{BASE_URL}/grader?session_id={session_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Score: {data['score']:.3f}")
        print(f"   Feedback: {data['feedback']}")
        print(f"   Lives Saved: {data['lives_saved']}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_metrics():
    print("\n6. Testing Metrics Endpoint...")
    response = requests.get(f"{BASE_URL}/metrics")
    metrics = response.json()
    print(f"   Total Episodes: {metrics['total_episodes']}")
    print(f"   Average Scores: Easy: {metrics['average_scores']['easy']:.3f}")
    return response.status_code == 200

if __name__ == "__main__":
    print("="*60)
    print("🚀 TESTING DISASTER RESPONSE ENVIRONMENT")
    print("="*60)
    
    # Ensure server is running first
    print("\n⚠️  Make sure the server is running: uvicorn server.app:app --reload")
    print("   Press Enter to continue...")
    input()
    
    all_passed = True
    
    try:
        all_passed &= test_health()
        all_passed &= test_tasks()
        session_id = test_reset()
        if session_id:
            all_passed &= test_step(session_id)
            all_passed &= test_grader(session_id)
        all_passed &= test_metrics()
        
        print("\n" + "="*60)
        if all_passed:
            print("🎉 ALL TESTS PASSED! Environment is ready!")
        else:
            print("⚠️ Some tests failed. Check the errors above.")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server. Is it running?")
        print("   Start server with: uvicorn server.app:app --reload")