#!/usr/bin/env python3
"""
Test script for multi-location testing
Run this after backend is running

Usage:
    python test_locations.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"
LOCATIONS = ["nellore", "bay_of_bengal_1", "chennai_coast"]

def test_location(location):
    """Test a single location"""
    try:
        url = f"{BASE_URL}/analyze/{location}"
        print(f"\n🔍 Testing {location}...")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {location}: SUCCESS")
            print(f"   Location: {data['location']['name']}")
            print(f"   Coordinates: ({data['location']['latitude']}, {data['location']['longitude']})")
            print(f"   Risk Level: {data['risk_assessment']['risk_level']}")
            print(f"   Anomaly: {data['detection']['anomaly_level']}")
            print(f"   Confidence: {data['detection']['confidence_score']:.2f}")
            print(f"   Indicators: {', '.join(data['indicators'])}")
            return True
        else:
            print(f"❌ {location}: FAILED (Status {response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ {location}: ERROR - {str(e)}")
        return False

def test_history():
    """Test history endpoint"""
    try:
        print("\n📊 Testing history endpoint...")
        url = f"{BASE_URL}/history?limit=5"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ History endpoint: SUCCESS")
            print(f"   Total records: {data['total_records']}")
            return True
        else:
            print(f"❌ History endpoint: FAILED")
            return False
    except Exception as e:
        print(f"❌ History endpoint: ERROR - {str(e)}")
        return False

def test_stats():
    """Test statistics endpoint"""
    try:
        print("\n📈 Testing stats endpoint...")
        url = f"{BASE_URL}/stats"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats endpoint: SUCCESS")
            print(f"   Total detections: {data['statistics']['total_detections']}")
            return True
        else:
            print(f"❌ Stats endpoint: FAILED")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint: ERROR - {str(e)}")
        return False

def test_health():
    """Test health endpoint"""
    try:
        print("\n❤️ Testing health endpoint...")
        url = f"{BASE_URL}/health"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint: SUCCESS")
            print(f"   Status: {data['status']}")
            print(f"   Database: {data['database']}")
            return True
        else:
            print(f"❌ Health endpoint: FAILED")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: ERROR - {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌊 OceanSentinel - Multi-Location Test Suite")
    print("="*70)
    
    # Test health first
    if not test_health():
        print("\n⚠️  Backend not responding. Make sure backend is running:")
        print("   python app.py")
        exit(1)
    
    # Test all locations
    results = []
    for location in LOCATIONS:
        results.append(test_location(location))
    
    # Test endpoints
    test_history()
    test_stats()
    
    # Summary
    print("\n" + "="*70)
    print(f"RESULTS: {sum(results)}/{len(results)} locations passed")
    print("="*70)
    
    if all(results):
        print("✅ All locations working! Ready for submission.")
        exit(0)
    else:
        print("❌ Some locations failed. Check errors above.")
        exit(1)