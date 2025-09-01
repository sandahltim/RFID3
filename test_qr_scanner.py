#!/usr/bin/env python3
"""
Test script for QR Scanner functionality
Tests the /api/item-lookup endpoint with sample data
"""
import requests
import json

def test_item_lookup():
    """Test the item lookup API endpoint"""
    
    # Test data
    test_queries = [
        "123456",  # Sample tag ID
        "RC001",   # Sample rental class
        "tent",    # Sample partial match
    ]
    
    base_url = "http://localhost:8101"
    endpoint = "/api/item-lookup"
    
    print("Testing QR Scanner Item Lookup API")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        try:
            payload = {
                "query": query,
                "source": "test_script"
            }
            
            response = requests.post(
                f"{base_url}{endpoint}",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success', 'Unknown')}")
                print(f"Items Found: {data.get('count', 0)}")
                print(f"Search Time: {data.get('search_time', 'Unknown')}ms")
                print(f"Tables Searched: {', '.join(data.get('searched_tables', []))}")
                
                if data.get('items'):
                    print("Sample item details:")
                    item = data['items'][0]
                    print(f"  - Tag ID: {item.get('tag_id', 'N/A')}")
                    print(f"  - Common Name: {item.get('common_name', 'N/A')}")
                    print(f"  - Status: {item.get('status', 'N/A')}")
                    
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed - make sure Flask app is running on port 8101")
            break
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("QR Scanner API Test Complete")

if __name__ == "__main__":
    test_item_lookup()