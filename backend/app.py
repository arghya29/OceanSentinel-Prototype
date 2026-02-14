"""
OceanSentinel Coastal Risk Monitoring API - Enhanced Version with Spatial Localization

IMPROVEMENTS IMPLEMENTED:
1. Pre-trained ML model with joblib persistence
3. Enhanced feature engineering (10 features vs 5)
4. Better confidence scoring using ML decision function
5. Enhanced risk scoring with temporal persistence and seasonal factors
6. REAL Sentinel-2 L2A satellite data from Sentinel Hub API
7. NEW: Spatial anomaly localization - tracks WHERE in image anomaly is detected
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import cv2
import os
from anomaly import detect_anomaly, analyze_specific_indicators
from risk import risk_score
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE = 'detections.db'

def init_database():
    """Initialize SQLite database with detections table"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Create detections table
        c.execute('''CREATE TABLE IF NOT EXISTS detections
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      location_id TEXT NOT NULL,
                      location_name TEXT NOT NULL,
                      risk_level TEXT NOT NULL,
                      anomaly_level TEXT NOT NULL,
                      confidence_score REAL NOT NULL,
                      detection_json TEXT NOT NULL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create index for better query performance (IMPROVEMENT from analysis)
        c.execute('''CREATE INDEX IF NOT EXISTS idx_location_time 
                     ON detections(location_id, timestamp)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_risk_level 
                     ON detections(risk_level)''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {DATABASE}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")

def save_detection(location_id, location_name, risk_level, anomaly_level, confidence_score, detection_json):
    """Save detection result to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute('''INSERT INTO detections 
                     (location_id, location_name, risk_level, anomaly_level, confidence_score, detection_json)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 (location_id, location_name, risk_level, anomaly_level, confidence_score, 
                  json.dumps(detection_json)))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved detection for {location_name}")
        return True
    except Exception as e:
        print(f"❌ Error saving detection: {str(e)}")
        return False

def get_detection_history(location_id=None, limit=50):
    """Retrieve detection history from database"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        if location_id:
            c.execute('''SELECT id, location_id, location_name, risk_level, anomaly_level, 
                         confidence_score, timestamp FROM detections 
                         WHERE location_id = ? 
                         ORDER BY timestamp DESC LIMIT ?''',
                     (location_id, limit))
        else:
            c.execute('''SELECT id, location_id, location_name, risk_level, anomaly_level, 
                         confidence_score, timestamp FROM detections 
                         ORDER BY timestamp DESC LIMIT ?''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'location_id': row[1],
                'location_name': row[2],
                'risk_level': row[3],
                'anomaly_level': row[4],
                'confidence_score': row[5],
                'timestamp': row[6]
            })
        
        return results
    except Exception as e:
        print(f"❌ Error retrieving history: {str(e)}")
        return []

def get_database_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM detections")
        total = c.fetchone()[0]
        
        c.execute('''SELECT risk_level, COUNT(*) FROM detections 
                     GROUP BY risk_level''')
        risk_counts = dict(c.fetchall())
        
        # Get anomaly breakdown
        c.execute('''SELECT anomaly_level, COUNT(*) FROM detections 
                     GROUP BY anomaly_level''')
        anomaly_counts = dict(c.fetchall())
        
        conn.close()
        
        return {
            'total_detections': total,
            'risk_breakdown': risk_counts,
            'anomaly_breakdown': anomaly_counts
        }
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return {'total_detections': 0, 'risk_breakdown': {}, 'anomaly_breakdown': {}}

# ============================================================================
# LOCATION CONFIGURATION WITH BOUNDING BOXES
# ============================================================================

# These match the bounding boxes used in fetch_sentinel_data.py
LOCATION_BBOXES = {
    "nellore": {
        "bbox": [79.8, 13.8, 80.8, 14.2],  # [west, south, east, north]
        "center_lat": 14.0,
        "center_lon": 80.3
    },
    "bay_of_bengal_1": {
        "bbox": [80.8, 15.0, 81.8, 15.4],
        "center_lat": 15.2,
        "center_lon": 81.5
    },
    "chennai_coast": {
        "bbox": [80.0, 12.8, 81.0, 13.2],
        "center_lat": 13.0,
        "center_lon": 80.5
    }
}

LOCATIONS = {
    "nellore": {
        "name": "Nellore Offshore Waters",
        "before": "data/real_satellite/nellore_before.jpg",
        "after": "data/real_satellite/nellore_after.jpg",
        "latitude": 14.0,  # Region center
        "longitude": 80.3,  # Region center
        "description": "Real Sentinel-2 L2A satellite data - Nellore coast",
        "source": "ESA Copernicus Sentinel-2",
        "data_before_date": "2026-01-14",
        "data_after_date": "2026-01-29",
        "resolution": "10m",
        "processing_level": "L2A (Atmospherically Corrected)"
    },
    "bay_of_bengal_1": {
        "name": "Bay of Bengal - Point 1",
        "before": "data/real_satellite/bay_of_bengal_1_before.jpg",
        "after": "data/real_satellite/bay_of_bengal_1_after.jpg",
        "latitude": 15.2,  # Region center
        "longitude": 81.5,  # Region center
        "description": "Real Sentinel-2 L2A satellite data - Open ocean monitoring",
        "source": "ESA Copernicus Sentinel-2",
        "data_before_date": "2026-01-28",
        "data_after_date": "2026-02-02",
        "resolution": "10m",
        "processing_level": "L2A (Atmospherically Corrected)"
    },
    "chennai_coast": {
        "name": "Chennai Offshore Waters",
        "before": "data/real_satellite/chennai_coast_before.jpg",
        "after": "data/real_satellite/chennai_coast_after.jpg",
        "latitude": 13.0,  # Region center
        "longitude": 80.5,  # Region center
        "description": "Real Sentinel-2 L2A satellite data - Chennai coast",
        "source": "ESA Copernicus Sentinel-2",
        "data_before_date": "2026-01-29",
        "data_after_date": "2026-02-03",
        "resolution": "10m",
        "processing_level": "L2A (Atmospherically Corrected)"
    }
}

# ============================================================================
# COORDINATE CONVERSION HELPER
# ============================================================================

def image_coords_to_latlon(normalized_x, normalized_y, bbox):
    """
    Convert normalized image coordinates (0-1) to geographic lat/lon
    
    Args:
        normalized_x: Horizontal position in image (0=left, 1=right)
        normalized_y: Vertical position in image (0=top, 1=bottom)
        bbox: [west, south, east, north] bounding box in degrees
    
    Returns:
        Tuple: (latitude, longitude)
    """
    west, south, east, north = bbox
    
    # Linear interpolation
    # X axis maps to longitude (west to east)
    lon = west + (east - west) * normalized_x
    
    # Y axis maps to latitude (north to south)
    # Note: Y is inverted in images (0=top=north, 1=bottom=south)
    lat = north - (north - south) * normalized_y
    
    return (lat, lon)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route("/", methods=["GET"])
def home():
    """API root endpoint"""
    return jsonify({
        "service": "OceanSentinel Coastal Risk Monitoring API",
        "version": "2.1.0-spatial-localization",
        "status": "operational",
        "features": [
            "Real Sentinel-2 satellite data",
            "Enhanced anomaly detection (10-feature ML model)",
            "Spatial anomaly localization (NEW)",
            "Temporal persistence tracking",
            "Seasonal risk factors",
            "Geospatial risk assessment"
        ],
        "endpoints": {
            "GET /": "API information",
            "GET /locations": "List available monitoring locations",
            "GET /analyze/<location>": "Analyze specific location",
            "POST /batch-analyze": "Analyze multiple locations",
            "GET /history": "Get detection history",
            "GET /history/<location>": "Get location-specific history",
            "GET /stats": "Get database statistics",
            "GET /images/<filename>": "Serve satellite images",
            "POST /send-alert": "Send alert notification"
        }
    })

@app.route("/locations", methods=["GET"])
def get_locations():
    """Get list of available locations"""
    locations_list = []
    for loc_id, loc_data in LOCATIONS.items():
        bbox_data = LOCATION_BBOXES.get(loc_id, {})
        locations_list.append({
            "id": loc_id,
            "name": loc_data["name"],
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "bbox": bbox_data.get("bbox", []),
            "description": loc_data["description"],
            "data_source": loc_data["source"]
        })
    
    return jsonify({
        "locations": locations_list,
        "count": len(locations_list)
    })

@app.route("/analyze/<location>", methods=["GET"])
def analyze_location(location):
    """
    Analyze a specific location using satellite imagery
    
    NEW: Now includes spatial localization - returns separate coordinates for:
    - Region center (for scanning visualization)
    - Anomaly location (actual detected position)
    """
    try:
        # Validate location
        if location not in LOCATIONS:
            return jsonify({
                "error": f"Unknown location: {location}",
                "available_locations": list(LOCATIONS.keys())
            }), 404
        
        loc_data = LOCATIONS[location]
        bbox_data = LOCATION_BBOXES.get(location, {})
        
        # Load satellite images
        before_img = cv2.imread(loc_data["before"])
        after_img = cv2.imread(loc_data["after"])
        
        if before_img is None or after_img is None:
            return jsonify({
                "error": "Satellite images not found",
                "location": location,
                "before_path": loc_data["before"],
                "after_path": loc_data["after"],
                "note": "Run fetch_sentinel_data.py to download real satellite data"
            }), 404
        
        # Perform anomaly detection with spatial localization
        anomaly_level, confidence_score, features, pixel_location = detect_anomaly(
            before_img, after_img
        )
        
        print(f"\n🔍 DEBUG - Spatial Localization:")
        print(f"   Pixel location: ({pixel_location['pixel_x']}, {pixel_location['pixel_y']})")
        print(f"   Normalized: ({pixel_location['normalized_x']:.3f}, {pixel_location['normalized_y']:.3f})")
        
        # Convert pixel location to geographic coordinates
        bbox = bbox_data.get("bbox", [])
        if bbox:
            anomaly_lat, anomaly_lon = image_coords_to_latlon(
                pixel_location['normalized_x'],
                pixel_location['normalized_y'],
                bbox
            )
            print(f"   Geographic: ({anomaly_lat:.4f}, {anomaly_lon:.4f})")
            
            # Calculate distance from region center
            from risk import calculate_distance
            distance_from_center = calculate_distance(
                loc_data["latitude"], loc_data["longitude"],
                anomaly_lat, anomaly_lon
            )
            print(f"   Distance from center: {distance_from_center:.2f} km")
        else:
            # Fallback to region center if no bbox
            anomaly_lat = loc_data["latitude"]
            anomaly_lon = loc_data["longitude"]
            distance_from_center = 0
            print("   ⚠️  No bbox available, using region center")
        
        # Analyze specific indicators
        indicators = analyze_specific_indicators(before_img, after_img)
        
        # Perform risk assessment
        risk_assessment = risk_score(
            anomaly_level, 
            anomaly_lat,  # Use anomaly location for risk assessment
            anomaly_lon,
            indicators,
            location_id=location,
            confidence=confidence_score,
            features=features
        )
        
        # Build comprehensive response
        response = {
            "location": {
                "id": location,
                "name": loc_data["name"],
                "region_center": {
                    "latitude": loc_data["latitude"],
                    "longitude": loc_data["longitude"]
                },
                "bbox": bbox,
                "description": loc_data["description"]
            },
            "detection": {
                "anomaly_level": anomaly_level,
                "confidence_score": confidence_score,
                "anomaly_location": {
                    "latitude": anomaly_lat,
                    "longitude": anomaly_lon,
                    "distance_from_center_km": round(distance_from_center, 2),
                    "pixel_coordinates": {
                        "x": pixel_location['pixel_x'],
                        "y": pixel_location['pixel_y']
                    },
                    "normalized_coordinates": {
                        "x": round(pixel_location['normalized_x'], 4),
                        "y": round(pixel_location['normalized_y'], 4)
                    }
                },
                "features": {
                    # Basic features
                    "mean_change": round(features["mean_change"], 2),
                    "std_deviation": round(features["std_change"], 2),
                    "max_change": round(features["max_change"], 2),
                    "edge_variance": round(features["edge_variance"], 2),
                    "significant_pixels_percent": round(features["significant_pixels"], 2),
                    # Enhanced features
                    "texture_complexity": round(features.get("texture_complexity", 0), 2),
                    "spectral_energy_change": round(features.get("spectral_energy_change", 0), 4),
                    "histogram_distance": round(features.get("histogram_distance", 0), 4),
                    "spatial_variance": round(features.get("spatial_variance", 0), 2),
                    "entropy_change": round(features.get("entropy_change", 0), 4)
                }
            },
            "indicators": indicators,
            "risk_assessment": risk_assessment,
            "satellite_data": {
                "source": loc_data["source"],
                "processing_level": loc_data["processing_level"],
                "before_date": loc_data["data_before_date"],
                "after_date": loc_data["data_after_date"],
                "resolution": loc_data["resolution"],
                "retrieval_method": "Sentinel Hub API",
                "location_description": loc_data["description"]
            },
            "model_info": {
                "type": "Isolation Forest (Pre-trained)",
                "features": "10-dimensional enhanced feature vector",
                "improvements": "Temporal persistence + Seasonal factors + Spatial localization"
            },
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        # Save to database
        save_detection(
            location_id=location,
            location_name=loc_data["name"],
            risk_level=risk_assessment['risk_level'],
            anomaly_level=anomaly_level,
            confidence_score=confidence_score,
            detection_json=response
        )
        
        return jsonify(response)
    
    except ValueError as ve:
        return jsonify({
            "error": str(ve),
            "status": "failed"
        }), 400
    
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "failed"
        }), 500

@app.route("/batch-analyze", methods=["POST"])
def batch_analyze():
    """Analyze multiple locations at once"""
    try:
        data = request.get_json()
        locations_to_analyze = data.get("locations", list(LOCATIONS.keys()))
        
        results = []
        
        for loc in locations_to_analyze:
            if loc in LOCATIONS:
                # Analyze location
                response = analyze_location(loc)
                if isinstance(response, tuple):
                    response_data, status_code = response
                    if status_code == 200:
                        results.append(response_data.get_json())
                else:
                    results.append(response.get_json())
        
        return jsonify({
            "batch_analysis": True,
            "total_analyzed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/history", methods=["GET"])
def get_history():
    """Get detection history (all locations)"""
    limit = request.args.get('limit', 50, type=int)
    history = get_detection_history(limit=limit)
    return jsonify({
        "history": history,
        "count": len(history)
    })

@app.route("/history/<location>", methods=["GET"])
def get_location_history(location):
    """Get detection history for specific location"""
    limit = request.args.get('limit', 50, type=int)
    history = get_detection_history(location_id=location, limit=limit)
    return jsonify({
        "location": location,
        "history": history,
        "count": len(history)
    })

@app.route("/stats", methods=["GET"])
def get_stats():
    """Get database statistics"""
    stats = get_database_stats()
    return jsonify(stats)

@app.route("/send-alert", methods=["POST"])
def send_alert():
    """
    Send alert notification (email/SMS)
    In production, this would integrate with actual notification services
    """
    try:
        data = request.get_json()
        
        alert_data = {
            "location": data.get("location", "Unknown"),
            "risk_level": data.get("risk_level", "UNKNOWN"),
            "confidence": data.get("confidence", 0),
            "action": data.get("action", "Monitor situation"),
            "timestamp": datetime.now().isoformat()
        }
        
        # In production: Send actual email/SMS here
        # For now, just log and return success
        print(f"\n🚨 ALERT TRIGGERED:")
        print(f"   Location: {alert_data['location']}")
        print(f"   Risk: {alert_data['risk_level']}")
        print(f"   Confidence: {alert_data['confidence']}")
        print(f"   Action: {alert_data['action']}\n")
        
        return jsonify({
            "status": "success",
            "message": "Alert notification sent",
            "alert_data": alert_data
        })
    
    except Exception as e:
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500

# ============================================================================
# IMAGE SERVING ENDPOINT
# ============================================================================

@app.route("/images/<filename>", methods=["GET"])
def serve_image(filename):
    """Serve satellite images for before/after comparison"""
    try:
        # Construct file path
        file_path = os.path.join("data", "real_satellite", filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                "error": f"Image not found: {filename}",
                "path": file_path,
                "note": "Make sure satellite images are in data/real_satellite/ directory"
            }), 404
        
        # Serve the image file
        return send_file(file_path, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({
            "error": f"Error serving image: {str(e)}"
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "status": 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "status": 500
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Check if data directories exist
    if not os.path.exists("data"):
        print("⚠️  WARNING: 'data' directory not found. Creating it...")
        os.makedirs("data")
    
    if not os.path.exists("data/real_satellite"):
        print("⚠️  WARNING: 'data/real_satellite' directory not found.")
        print("   Please run 'python fetch_sentinel_data.py' to download real Sentinel-2 data")
    
    print("\n" + "="*70)
    print("🌊 OceanSentinel Coastal Risk Monitoring API - ENHANCED VERSION")
    print("="*70)
    print(f"📍 Available locations: {list(LOCATIONS.keys())}")
    print(f"💾 Database: {DATABASE}")
    print(f"🛰️  Data source: Real Sentinel-2 L2A (ESA Copernicus Sentinel Hub API)")
    print(f"🚀 Server running on http://localhost:5000")
    print(f"📊 API Version: 2.1.0-spatial-localization")
    print("\nIMPROVEMENTS:")
    print("  ✅ Real Sentinel-2 satellite data from Sentinel Hub API")
    print("  ✅ Pre-trained ML model (Isolation Forest)")
    print("  ✅ Enhanced features (10 vs 5)")
    print("  ✅ Better confidence scoring")
    print("  ✅ Temporal persistence tracking")
    print("  ✅ Seasonal risk factors")
    print("  ✅ Indicator-specific weighting")
    print("  ✅ NEW: Spatial anomaly localization")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)