#!/usr/bin/env python3
"""
Test script for bulk label insertion functionality
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
AUTH = ("admin@karsaaz.com", "Admin123")

def test_bulk_insert():
    """Test the bulk insert endpoint"""
    
    # Test data
    bulk_data = {
        "language_id": 1,
        "label_group_id": 1,
        "labels": [
            {
                "label_code_name": "test_bulk_1",
                "label_text": "Test Bulk Label 1"
            },
            {
                "label_code_name": "test_bulk_2",
                "label_text": "Test Bulk Label 2"
            },
            {
                "label_code_name": "test_bulk_3",
                "label_text": "Test Bulk Label 3"
            }
        ]
    }
    
    try:
        print("🚀 Testing bulk insert endpoint...")
        
        response = requests.post(
            f"{BASE_URL}/api/labels/bulk-insert",
            json=bulk_data,
            auth=AUTH,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Bulk insert successful!")
            print(f"Total labels: {result['total_labels']}")
            print(f"Successful: {result['successful_insertions']}")
            print(f"Failed: {result['failed_insertions']}")
            print(f"Message: {result['message']}")
            
            if result['results']:
                print("\n📊 Detailed Results:")
                for item in result['results']:
                    status = "✅" if item['success'] else "❌"
                    print(f"  {status} {item['label_code_name']}: {item['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🏥 Testing server health...")
    test_health()
    print("\n" + "="*50 + "\n")
    test_bulk_insert() 