#!/usr/bin/env python3
"""
Script to test the Travel Planner API endpoints directly.
This can be used to debug API issues without going through the frontend.
"""

import requests
import json
import argparse
import sys

def setup_args():
    parser = argparse.ArgumentParser(description='Test Travel Planner API endpoints')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--token', required=True, help='Authentication token')
    parser.add_argument('--user-id', required=True, help='User ID to test with')
    parser.add_argument('--endpoint', choices=['trips', 'trip', 'create', 'update', 'delete'], 
                        default='trips', help='Endpoint to test')
    parser.add_argument('--trip-id', help='Trip ID for trip-specific operations')
    return parser.parse_args()

def get_headers(token):
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

def test_get_trips(base_url, headers, user_id):
    """Test getting all trips for a user"""
    url = f"{base_url}/trips/user/{user_id}"
    print(f"Testing GET {url}")
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        trips = response.json()
        print(f"Found {len(trips)} trips")
        if trips:
            print(f"First trip: {json.dumps(trips[0], indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_get_trip(base_url, headers, trip_id):
    """Test getting a specific trip"""
    url = f"{base_url}/trips/{trip_id}"
    print(f"Testing GET {url}")
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        trip = response.json()
        print(f"Trip details: {json.dumps(trip, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_create_trip(base_url, headers, user_id):
    """Test creating a new trip"""
    url = f"{base_url}/trips"
    print(f"Testing POST {url}")
    
    # Sample trip data
    trip_data = {
        "userId": user_id,
        "formData": {
            "destination": "Test Destination",
            "startDate": "2023-06-01",
            "endDate": "2023-06-07",
            "travelType": "flight",
            "adults": 2,
            "children": 0,
            "infants": 0,
            "budget": "mid-range",
            "budgetLevel": "mid-range",
            "language": "en",
            "entertainmentPreferences": ["cultural", "outdoor"],
            "intermediateStops": []
        },
        "itinerary": {
            "tripId": "test-trip",
            "days": [
                {
                    "date": "2023-06-01",
                    "activities": [
                        {
                            "id": "activity-1",
                            "time": "09:00",
                            "description": "Arrive at destination",
                            "type": "travel"
                        }
                    ]
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=trip_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        created_trip = response.json()
        print(f"Created trip: {json.dumps(created_trip, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_update_trip(base_url, headers, user_id, trip_id):
    """Test updating an existing trip"""
    url = f"{base_url}/trips/{trip_id}"
    print(f"Testing PUT {url}")
    
    # First get the existing trip
    get_response = requests.get(f"{base_url}/trips/{trip_id}", headers=headers)
    if get_response.status_code != 200:
        print(f"Error getting trip to update: {get_response.text}")
        return get_response
    
    existing_trip = get_response.json()
    
    # Update the destination
    update_data = {
        "userId": user_id,
        "formData": {
            **existing_trip["formData"],
            "destination": f"Updated Destination {int(time.time())}"
        },
        "itinerary": existing_trip["itinerary"]
    }
    
    response = requests.put(url, headers=headers, json=update_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        updated_trip = response.json()
        print(f"Updated trip: {json.dumps(updated_trip, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_delete_trip(base_url, headers, trip_id):
    """Test deleting a trip"""
    url = f"{base_url}/trips/{trip_id}"
    print(f"Testing DELETE {url}")
    
    response = requests.delete(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    return response

def main():
    args = setup_args()
    headers = get_headers(args.token)
    
    if args.endpoint == 'trips':
        test_get_trips(args.url, headers, args.user_id)
    elif args.endpoint == 'trip':
        if not args.trip_id:
            print("Error: --trip-id is required for this endpoint")
            sys.exit(1)
        test_get_trip(args.url, headers, args.trip_id)
    elif args.endpoint == 'create':
        test_create_trip(args.url, headers, args.user_id)
    elif args.endpoint == 'update':
        if not args.trip_id:
            print("Error: --trip-id is required for this endpoint")
            sys.exit(1)
        test_update_trip(args.url, headers, args.user_id, args.trip_id)
    elif args.endpoint == 'delete':
        if not args.trip_id:
            print("Error: --trip-id is required for this endpoint")
            sys.exit(1)
        test_delete_trip(args.url, headers, args.trip_id)

if __name__ == "__main__":
    import time  # Import here to avoid unused import warning
    main() 