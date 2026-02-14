"""
Fetch real Sentinel-2 data from Sentinel Hub API
This script downloads actual satellite imagery for your 3 locations
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import cv2
import numpy as np
from pathlib import Path

# Load credentials from .env file
load_dotenv()

CLIENT_ID = os.getenv('SENTINEL_HUB_CLIENT_ID')
CLIENT_SECRET = os.getenv('SENTINEL_HUB_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ERROR: Missing Sentinel Hub credentials!")
    print("Please create a .env file with:")
    print("  SENTINEL_HUB_CLIENT_ID=your_id")
    print("  SENTINEL_HUB_CLIENT_SECRET=your_secret")
    exit(1)

# ============================================================================
# LOCATION DEFINITIONS - These are REAL Bay of Bengal coordinates
# ============================================================================

LOCATIONS = {
    "nellore": {
        "name": "Nellore Offshore Waters",
        "bbox": [79.8, 13.8, 80.8, 14.2],  # [west, south, east, north]
        "lat": 14.0,
        "lon": 80.3,
        "description": "Coastal area east of Nellore, Andhra Pradesh"
    },
    "bay_of_bengal_1": {
        "name": "Bay of Bengal - Point 1",
        "bbox": [80.8, 15.0, 81.8, 15.4],
        "lat": 15.2,
        "lon": 81.5,
        "description": "Open ocean monitoring point in Bay of Bengal"
    },
    "chennai_coast": {
        "name": "Chennai Offshore Waters",
        "bbox": [80.0, 12.8, 81.0, 13.2],
        "lat": 13.0,
        "lon": 80.5,
        "description": "Coastal area east of Chennai, Tamil Nadu"
    }
}

# Date range for analysis
DATE_BEFORE = "2026-01-05"
DATE_AFTER = "2026-01-30"

# ============================================================================
# AUTHENTICATION & REQUEST BUILDER
# ============================================================================

class SentinelHubRequester:
    """Handle authentication and API requests to Sentinel Hub"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        
    def get_access_token(self):
        """Authenticate and get access token"""
        
        url = "https://services.sentinel-hub.com/oauth/token"
        
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        print("🔐 Authenticating with Sentinel Hub...")
        
        response = requests.post(url, data=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            print("✅ Authentication successful!")
            return self.access_token
        else:
            print(f"❌ Authentication failed: {response.text}")
            exit(1)
    
    def build_evalscript(self):
        """
        Create evalscript that Sentinel Hub understands
        This extracts RGB bands and handles clouds
        """
        
        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B02", "B03", "B04", "CLM"],
            output: {
              bands: 3,
              sampleType: "UINT8"
            }
          }
        }
        
        function evaluatePixel(sample) {
          // Check if pixel is cloudy
          if (sample.CLM == 1) {
            // Return light blue for clouds
            return [180, 220, 255];
          }
          
          // Return RGB (B04=Red, B03=Green, B02=Blue)
          // Scale from 0-10000 range to 0-255
          return [
            Math.floor(sample.B04 / 10000 * 255),
            Math.floor(sample.B03 / 10000 * 255),
            Math.floor(sample.B02 / 10000 * 255)
          ];
        }
        """
        
        return evalscript

def fetch_sentinel2_data(location_key, date_string):
    """
    Fetch Sentinel-2 data for a specific location and date
    
    Args:
        location_key: 'nellore', 'bay_of_bengal_1', or 'chennai_coast'
        date_string: '2026-01-05' format
    
    Returns:
        Image as numpy array (BGR format, ready for OpenCV)
    """
    
    loc = LOCATIONS[location_key]
    
    # Get access token
    requester = SentinelHubRequester(CLIENT_ID, CLIENT_SECRET)
    token = requester.get_access_token()
    
    # Build the request payload
    payload = {
        "evalscript": requester.build_evalscript(),
        "input": {
            "bounds": {
                "bbox": loc["bbox"],
                "properties": {"crs": "http://www.opengis.net/gml/srs/epsg.xml#4326"}
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date_string}T00:00:00Z",
                            "to": f"{date_string}T23:59:59Z"
                        },
                        "maxCloudCoverage": 30  # Only use images with < 30% cloud cover
                    }
                }
            ]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/jpeg"}}]
        }
    }
    
    # Make request to Sentinel Hub API
    url = "https://services.sentinel-hub.com/api/v1/process"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"  📡 Fetching data for {location_key} ({date_string})...")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code == 200:
        # Response is JPEG image bytes
        # Save to temporary array
        image_array = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        print(f"  ✅ Retrieved {image.shape[1]}x{image.shape[0]} image")
        return image
    else:
        print(f"  ❌ Failed to fetch data: {response.status_code}")
        print(f"     Response: {response.text}")
        return None

def main():
    """Main execution - fetch all data"""
    
    print("\n" + "="*70)
    print("🛰️  SENTINEL HUB REAL SATELLITE DATA FETCHER")
    print("="*70)
    
    # Create output directory
    output_dir = Path("data/real_satellite")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Output directory: {output_dir.absolute()}\n")
    
    # Fetch for each location
    for location_key, loc_data in LOCATIONS.items():
        print(f"\n🌍 Location: {loc_data['name']}")
        print(f"   Bbox: {loc_data['bbox']}")
        print(f"   Coords: ({loc_data['lat']}, {loc_data['lon']})")
        
        # Fetch BEFORE image
        print(f"\n  📅 Date BEFORE: {DATE_BEFORE}")
        before_image = fetch_sentinel2_data(location_key, DATE_BEFORE)
        
        if before_image is None:
            print(f"  ⚠️  Skipping {location_key} - no data available")
            continue
        
        # Fetch AFTER image
        print(f"  📅 Date AFTER:  {DATE_AFTER}")
        after_image = fetch_sentinel2_data(location_key, DATE_AFTER)
        
        if after_image is None:
            print(f"  ⚠️  Skipping {location_key} - no data available")
            continue
        
        # Save to disk
        before_path = output_dir / f"{location_key}_before.jpg"
        after_path = output_dir / f"{location_key}_after.jpg"
        
        cv2.imwrite(str(before_path), before_image)
        cv2.imwrite(str(after_path), after_image)
        
        print(f"\n  💾 Saved:")
        print(f"     {before_path}")
        print(f"     {after_path}")
        print(f"  ✅ {location_key} complete!\n")
    
    print("\n" + "="*70)
    print("✅ DONE! All satellite data downloaded to data/real_satellite/")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()