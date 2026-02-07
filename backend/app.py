"""
OceanSentinel Coastal Risk Monitoring API - Enhanced Version

IMPROVEMENTS IMPLEMENTED:
1. Pre-trained ML model with joblib persistence
3. Enhanced feature engineering (10 features vs 5)
4. Better confidence scoring using ML decision function
5. Enhanced risk scoring with temporal persistence and seasonal factors

A Flask-based REST API that:
1. Analyzes satellite imagery for marine anomalies
2. Extracts enhanced computer vision features from image differences
3. Uses pre-trained ML (Isolation Forest) to detect anomalies
4. Assesses risk based on geospatial proximity, temporal persistence, and seasonal factors
5. Persists results to SQLite database
6. Sends alert notifications for high-risk detections
7. Supports multi-location monitoring
"""

from flask import Flask, jsonify, request
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
# LOCATION CONFIGURATION - MULTI-LOCATION SUPPORT
# ============================================================================

LOCATIONS = {
    "nellore": {
        "name": "Nellore Offshore Waters",
        "before": "data/image_before.jpg",
        "after": "data/image_after.jpg",
        "latitude": 14.0,
        "longitude": 80.3,
        "description": "Ocean waters east of Nellore coast"
    },
    "bay_of_bengal_1": {
        "name": "Bay of Bengal - Point 1",
        "before": "data/image_before.jpg",
        "after": "data/image_after.jpg",
        "latitude": 15.2,
        "longitude": 81.5,
        "description": "Open ocean monitoring point"
    },
    "chennai_coast": {
        "name": "Chennai Offshore Waters",
        "before": "data/image_before.jpg",
        "after": "data/image_after.jpg",
        "latitude": 13.0,
        "longitude": 80.5,
        "description": "Ocean waters east of Chennai coast"
    }
}

# ============================================================================
# ALERT NOTIFICATION SYSTEM
# ============================================================================

def simulate_email_alert(location_name, risk_level, confidence_score, recommended_action):
    """Simulate sending email alert"""
    email_content = f"""
    OceanSentinel Email Alert
    {'='*50}
    
    Location: {location_name}
    Risk Level: {risk_level}
    Confidence Score: {confidence_score:.2f}
    Timestamp: {datetime.now().isoformat()}
    
    RECOMMENDED ACTION:
    {recommended_action}
    
    Please review satellite imagery and contact coastal authorities
    if immediate action is required.
    
    OceanSentinel System
    """
    print(f"📧 EMAIL ALERT SENT:\n{email_content}")
    return True

def simulate_sms_alert(location_name, risk_level, confidence_score):
    """Simulate sending SMS alert"""
    sms_text = f"OceanSentinel: {location_name} - Risk {risk_level} detected (Score: {confidence_score:.2f}). Check dashboard for details."
    print(f"📱 SMS ALERT SENT: {sms_text}")
    return True

def create_dashboard_notification(location_name, risk_level, confidence_score, recommended_action):
    """Create dashboard notification"""
    notification = {
        "type": "HIGH_RISK_ALERT",
        "location": location_name,
        "risk_level": risk_level,
        "confidence_score": confidence_score,
        "message": f"High-risk anomaly detected at {location_name}",
        "action": recommended_action,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    print(f"🔔 DASHBOARD NOTIFICATION CREATED: {location_name}")
    return notification

# ============================================================================
# API ROUTES
# ============================================================================

@app.route("/")
def home():
    """API information endpoint"""
    return jsonify({
        "service": "OceanSentinel Coastal Risk Monitoring API",
        "version": "2.0.0-enhanced",
        "improvements": [
            "Pre-trained ML model with joblib persistence",
            "Enhanced feature engineering (10 features)",
            "Better confidence scoring using ML decision function",
            "Temporal persistence tracking",
            "Seasonal risk factors",
            "Indicator-specific weighting"
        ],
        "endpoints": {
            "GET /": "API information",
            "GET /health": "System health check",
            "GET /locations": "List all monitoring locations",
            "GET /analyze/<location>": "Analyze specific location",
            "GET /analyze": "Analyze default location (nellore)",
            "GET /history": "Get detection history",
            "GET /history/<location>": "Get history for specific location",
            "GET /stats": "Get database statistics",
            "POST /send-alert": "Send alert notifications",
            "POST /batch-analyze": "Analyze multiple locations"
        },
        "database": DATABASE,
        "model": "Isolation Forest (pre-trained)",
        "features": "10-dimensional enhanced feature vector"
    })

@app.route("/health")
def health_check():
    """System health check"""
    try:
        # Check database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM detections")
        count = c.fetchone()[0]
        conn.close()
        
        # Check if model exists
        model_exists = os.path.exists('models/anomaly_detector.pkl')
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "total_detections": count,
            "model_status": "loaded" if model_exists else "will train on first use",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route("/locations")
def get_locations():
    """Get all available monitoring locations"""
    locations_info = []
    for loc_id, loc_data in LOCATIONS.items():
        locations_info.append({
            "id": loc_id,
            "name": loc_data["name"],
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "description": loc_data["description"]
        })
    
    return jsonify({
        "total_locations": len(locations_info),
        "locations": locations_info
    })

@app.route("/history")
def get_history():
    """Get detection history for all locations"""
    limit = request.args.get('limit', 50, type=int)
    history = get_detection_history(limit=limit)
    
    return jsonify({
        "total_records": len(history),
        "history": history
    })

@app.route("/history/<location>")
def get_location_history(location):
    """Get detection history for specific location"""
    limit = request.args.get('limit', 50, type=int)
    
    if location not in LOCATIONS:
        return jsonify({
            "error": f"Location '{location}' not found",
            "available_locations": list(LOCATIONS.keys())
        }), 404
    
    history = get_detection_history(location_id=location, limit=limit)
    
    return jsonify({
        "location": location,
        "total_records": len(history),
        "history": history
    })

@app.route("/stats")
def get_stats():
    """Get database statistics"""
    stats = get_database_stats()
    
    return jsonify({
        "status": "success",
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/send-alert", methods=["POST"])
def send_alert():
    """Send alert notifications (Email, SMS, Dashboard)"""
    try:
        data = request.get_json()
        location = data.get("location")
        risk_level = data.get("risk_level")
        confidence = data.get("confidence")
        action = data.get("action", "Review satellite imagery immediately")
        
        if not location or not risk_level:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: location, risk_level"
            }), 400
        
        # Send simulated alerts
        email_sent = simulate_email_alert(location, risk_level, confidence, action)
        sms_sent = simulate_sms_alert(location, risk_level, confidence)
        notification = create_dashboard_notification(location, risk_level, confidence, action)
        
        return jsonify({
            "status": "success",
            "message": f"Alerts sent for {location}",
            "alerts": {
                "email": email_sent,
                "sms": sms_sent,
                "dashboard": True
            },
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/analyze")
def analyze_default():
    """Analyze default location (Nellore)"""
    return analyze_location("nellore")

@app.route("/analyze/<location>")
def analyze_location(location):
    """
    Analyze a specific location for marine anomalies
    
    ENHANCED VERSION with:
    - 10 enhanced features (vs 5 basic)
    - Pre-trained ML model
    - Better confidence scoring
    - Temporal persistence checking
    - Seasonal risk factors
    - Indicator-specific weighting
    
    Returns:
    - Location information
    - Detection results (anomaly level, confidence score, enhanced features)
    - Ocean-specific indicators
    - Enhanced risk assessment with multiple factors
    - Satellite metadata
    - Timestamp
    """
    try:
        # Validate location
        if location not in LOCATIONS:
            return jsonify({
                "error": f"Location '{location}' not found",
                "available_locations": list(LOCATIONS.keys())
            }), 404
        
        loc_data = LOCATIONS[location]
        
        # Load satellite images
        before_path = loc_data["before"]
        after_path = loc_data["after"]
        
        if not os.path.exists(before_path) or not os.path.exists(after_path):
            return jsonify({
                "error": "Satellite images not found for this location",
                "location": location,
                "expected_paths": {
                    "before": before_path,
                    "after": after_path
                }
            }), 404
        
        before = cv2.imread(before_path)
        after = cv2.imread(after_path)
        
        if before is None or after is None:
            return jsonify({
                "error": "Failed to load satellite images"
            }), 500
        
        # Perform enhanced anomaly detection
        anomaly_level, confidence_score, features = detect_anomaly(
            before, after, use_enhanced_features=True
        )
        
        # Analyze specific indicators
        indicators = analyze_specific_indicators(before, after)
        
        # Calculate enhanced risk with geospatial context, persistence, and seasonal factors
        risk_assessment = risk_score(
            anomaly_level, 
            loc_data["latitude"], 
            loc_data["longitude"],
            indicators,
            location_id=location,  # For persistence checking
            confidence=confidence_score,  # For enhanced scoring
            features=features  # For enhanced scoring
        )
        
        # Build comprehensive response
        response = {
            "location": {
                "id": location,
                "name": loc_data["name"],
                "latitude": loc_data["latitude"],
                "longitude": loc_data["longitude"],
                "description": loc_data["description"]
            },
            "detection": {
                "anomaly_level": anomaly_level,
                "confidence_score": confidence_score,
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
                "source": "Sentinel-2 L2A",
                "before_date": "2026-01-05",
                "after_date": "2026-01-30",
                "resolution": "10m"
            },
            "model_info": {
                "type": "Isolation Forest (Pre-trained)",
                "features": "10-dimensional enhanced feature vector",
                "improvements": "Temporal persistence + Seasonal factors + Indicator weighting"
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
    """
    Analyze multiple locations at once
    """
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
    
    # Check if data directory exists
    if not os.path.exists("data"):
        print("⚠️  WARNING: 'data' directory not found. Creating it...")
        os.makedirs("data")
        print("Please add satellite images to the 'data' folder")
    
    print("\n" + "="*70)
    print("🌊 OceanSentinel Coastal Risk Monitoring API - ENHANCED VERSION")
    print("="*70)
    print(f"📍 Available locations: {list(LOCATIONS.keys())}")
    print(f"💾 Database: {DATABASE}")
    print(f"🚀 Server running on http://localhost:5000")
    print(f"📊 API Version: 2.0.0-enhanced")
    print("\nIMPROVEMENTS:")
    print("  ✅ Pre-trained ML model (Isolation Forest)")
    print("  ✅ Enhanced features (10 vs 5)")
    print("  ✅ Better confidence scoring")
    print("  ✅ Temporal persistence tracking")
    print("  ✅ Seasonal risk factors")
    print("  ✅ Indicator-specific weighting")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)