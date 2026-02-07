#!/usr/bin/env python3
"""
Test script for database persistence
Checks if detections are being saved to database

Usage:
    python test_database.py
"""

import requests
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:5000"
DATABASE = 'detections.db'
LOCATIONS = ["nellore", "bay_of_bengal_1", "chennai_coast"]

def test_all_locations():
    """Analyze all locations"""
    print("\n📍 Testing all locations...")
    for location in LOCATIONS:
        try:
            response = requests.get(f"{BASE_URL}/analyze/{location}")
            if response.status_code == 200:
                print(f"   ✅ {location}: Analyzed")
            else:
                print(f"   ❌ {location}: Failed")
        except Exception as e:
            print(f"   ❌ {location}: Error - {str(e)}")

def check_database():
    """Check what's in the database"""
    print("\n" + "="*70)
    print("DATABASE CONTENTS")
    print("="*70 + "\n")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Get total count
        c.execute("SELECT COUNT(*) FROM detections")
        total = c.fetchone()[0]
        print(f"Total detections stored: {total}\n")
        
        # Get all records
        c.execute("""SELECT id, location_name, risk_level, anomaly_level, 
                    confidence_score, timestamp 
                    FROM detections 
                    ORDER BY timestamp DESC LIMIT 10""")
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            print("Recent Detections:")
            print("-" * 70)
            for i, row in enumerate(rows, 1):
                print(f"{i}. {row[1]} ({row[0]})")
                print(f"   Risk: {row[2]} | Anomaly: {row[3]} | Score: {row[4]:.2f}")
                print(f"   Time: {row[5]}\n")
            return True
        else:
            print("No detections in database yet.")
            return False
    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")
        return False

def get_statistics():
    """Get database statistics"""
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70 + "\n")
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Total
        c.execute("SELECT COUNT(*) FROM detections")
        total = c.fetchone()[0]
        print(f"Total detections: {total}")
        
        # By risk level
        c.execute("SELECT risk_level, COUNT(*) FROM detections GROUP BY risk_level")
        risk_breakdown = c.fetchall()
        if risk_breakdown:
            print("\nRisk Breakdown:")
            for risk, count in risk_breakdown:
                print(f"  {risk}: {count}")
        
        # By location
        c.execute("SELECT location_name, COUNT(*) FROM detections GROUP BY location_name")
        location_breakdown = c.fetchall()
        if location_breakdown:
            print("\nBy Location:")
            for location, count in location_breakdown:
                print(f"  {location}: {count}")
        
        # By anomaly
        c.execute("SELECT anomaly_level, COUNT(*) FROM detections GROUP BY anomaly_level")
        anomaly_breakdown = c.fetchall()
        if anomaly_breakdown:
            print("\nBy Anomaly Level:")
            for anomaly, count in anomaly_breakdown:
                print(f"  {anomaly}: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌊 OceanSentinel - Database Persistence Test")
    print("="*70)
    
    # Test all locations
    test_all_locations()
    
    # Check database
    if check_database():
        print("✅ Database persistence working!")
    else:
        print("❌ No data in database yet. Make sure you ran test_locations.py first.")
    
    # Get statistics
    get_statistics()
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70 + "\n")