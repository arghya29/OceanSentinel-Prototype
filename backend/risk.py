import math
from datetime import datetime, timedelta
import sqlite3

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers
    Using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance

def check_sensitive_zones(latitude, longitude):
    """
    Check if location is near sensitive coastal areas
    """
    # Define sensitive zones (expanded list)
    sensitive_zones = [
        {
            "name": "Pulicat Lake Bird Sanctuary",
            "lat": 13.6,
            "lon": 80.3,
            "radius_km": 15,
            "type": "Wildlife Protected Area"
        },
        {
            "name": "Coastal Fishing Villages",
            "lat": 14.4,
            "lon": 79.95,
            "radius_km": 10,
            "type": "Human Settlement"
        },
        {
            "name": "Mangrove Conservation Zone",
            "lat": 15.1,
            "lon": 81.0,
            "radius_km": 8,
            "type": "Ecological Reserve"
        },
        {
            "name": "Aquaculture Farms",
            "lat": 15.3,
            "lon": 81.2,
            "radius_km": 5,
            "type": "Economic Zone"
        },
        {
            "name": "Coral Reef Area",
            "lat": 13.2,
            "lon": 80.6,
            "radius_km": 12,
            "type": "Ecological Reserve"
        }
    ]
    
    nearby_zones = []
    closest_distance = float('inf')
    
    for zone in sensitive_zones:
        distance = calculate_distance(latitude, longitude, zone["lat"], zone["lon"])
        
        if distance < zone["radius_km"]:
            nearby_zones.append({
                "name": zone["name"],
                "type": zone["type"],
                "distance_km": round(distance, 2)
            })
            
            if distance < closest_distance:
                closest_distance = distance
    
    return nearby_zones, closest_distance

def check_persistent_anomaly(location_id, history_days=3, database='detections.db'):
    """
    IMPROVEMENT 5: Check if anomaly has persisted over multiple days
    
    Args:
        location_id: Location identifier
        history_days: Number of days to check back
        database: Database path
    
    Returns:
        Boolean indicating if anomaly is persistent
    """
    try:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        
        # Get detections from the last N days
        cutoff_date = datetime.now() - timedelta(days=history_days)
        
        c.execute('''
            SELECT anomaly_level FROM detections 
            WHERE location_id = ? 
            AND timestamp > ?
            ORDER BY timestamp DESC
        ''', (location_id, cutoff_date.isoformat()))
        
        recent_anomalies = c.fetchall()
        conn.close()
        
        # Check if we have multiple HIGH or MEDIUM detections
        if len(recent_anomalies) >= 2:
            high_medium_count = sum(1 for (level,) in recent_anomalies 
                                   if level in ['HIGH', 'MEDIUM'])
            if high_medium_count >= 2:
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking persistence: {e}")
        return False

def get_seasonal_risk_multiplier(current_date=None):
    """
    IMPROVEMENT 5: Apply seasonal risk factors
    
    Different seasons have different risk profiles for coastal anomalies:
    - Monsoon season (June-September): Higher risk of sediment plumes, algal blooms
    - Summer (March-May): Higher risk of thermal stress, coral bleaching
    - Winter (November-February): Lower baseline risk
    - Post-monsoon (October): Transition period
    
    Returns:
        Float multiplier (0.8 to 1.3)
    """
    if current_date is None:
        current_date = datetime.now()
    
    month = current_date.month
    
    # Define seasonal multipliers for Bay of Bengal region
    seasonal_factors = {
        # Winter (November-February): Low risk period
        11: 0.9, 12: 0.8, 1: 0.8, 2: 0.9,
        
        # Summer (March-May): High thermal stress
        3: 1.1, 4: 1.2, 5: 1.2,
        
        # Southwest Monsoon (June-September): High risk
        6: 1.3, 7: 1.3, 8: 1.2, 9: 1.2,
        
        # Post-monsoon (October): Transition
        10: 1.0
    }
    
    return seasonal_factors.get(month, 1.0)

def get_indicator_severity_weight(indicators):
    """
    IMPROVEMENT 5: Weight risk by type of indicator detected
    
    Different indicators have different severity levels:
    - Algal blooms: High ecological concern (1.3x)
    - Temperature anomalies: High concern for coral/marine life (1.2x)
    - Reflectance anomalies: Medium concern (1.1x)
    
    Returns:
        Float multiplier (1.0 to 1.3)
    """
    if not indicators or indicators == ["No specific indicators detected"]:
        return 1.0
    
    max_weight = 1.0
    
    for indicator in indicators:
        indicator_lower = indicator.lower()
        
        if "algal bloom" in indicator_lower:
            max_weight = max(max_weight, 1.3)
        elif "temperature" in indicator_lower or "thermal" in indicator_lower:
            max_weight = max(max_weight, 1.2)
        elif "reflectance" in indicator_lower:
            max_weight = max(max_weight, 1.1)
    
    return max_weight

def calculate_enhanced_risk_score(base_anomaly, confidence, features, indicators):
    """
    IMPROVEMENT 5: Enhanced risk calculation incorporating multiple factors
    
    Factors considered:
    1. Base anomaly level from ML
    2. Confidence score
    3. Feature magnitudes
    4. Indicator types
    
    Returns:
        Numerical risk score (0-100)
    """
    # Base score from anomaly level
    base_scores = {
        'HIGH': 70,
        'MEDIUM': 40,
        'LOW': 10
    }
    
    base_score = base_scores.get(base_anomaly, 10)
    
    # Factor in confidence
    confidence_factor = confidence / 100
    
    # Factor in feature magnitudes
    feature_score = (
        min(features.get('mean_change', 0) / 50 * 20, 20) +
        min(features.get('significant_pixels', 0) / 30 * 15, 15) +
        min(features.get('max_change', 0) / 100 * 10, 10)
    )
    
    # Indicator severity
    indicator_weight = get_indicator_severity_weight(indicators)
    
    # Calculate final score
    final_score = (base_score + feature_score) * confidence_factor * indicator_weight
    
    return min(100, round(final_score, 2))

def risk_score(anomaly_level, latitude, longitude, indicators=None, location_id=None, confidence=None, features=None):
    """
    Enhanced risk scoring with:
    - Geospatial context (ORIGINAL)
    - Temporal persistence (IMPROVEMENT 5)
    - Seasonal factors (IMPROVEMENT 5)
    - Indicator-specific weighting (IMPROVEMENT 5)
    """
    nearby_zones, closest_distance = check_sensitive_zones(latitude, longitude)
    
    # Base risk from anomaly detection
    base_risk = anomaly_level
    
    # IMPROVEMENT 5: Calculate enhanced risk score
    if confidence is not None and features is not None:
        numerical_risk_score = calculate_enhanced_risk_score(
            base_risk, confidence, features, indicators or []
        )
    else:
        # Fallback to simple scoring
        numerical_risk_score = {'HIGH': 70, 'MEDIUM': 40, 'LOW': 10}.get(base_risk, 10)
    
    # IMPROVEMENT 5: Check for persistent anomalies
    is_persistent = False
    persistence_note = ""
    if location_id:
        is_persistent = check_persistent_anomaly(location_id, history_days=3)
        if is_persistent:
            numerical_risk_score *= 1.5
            persistence_note = " (Persistent anomaly - detected multiple times in past 3 days)"
    
    # IMPROVEMENT 5: Apply seasonal factor
    seasonal_multiplier = get_seasonal_risk_multiplier()
    numerical_risk_score *= seasonal_multiplier
    
    # IMPROVEMENT 5: Apply indicator-specific weighting
    indicator_multiplier = get_indicator_severity_weight(indicators or [])
    numerical_risk_score *= indicator_multiplier
    
    # Cap at 100
    numerical_risk_score = min(100, numerical_risk_score)
    
    # Enhance risk if near sensitive zones
    near_sensitive = len(nearby_zones) > 0
    very_close = closest_distance < 5  # Within 5km
    
    # Risk escalation logic with enhanced scoring
    if numerical_risk_score >= 70 or base_risk == "HIGH":
        if very_close:
            final_risk = "CRITICAL"
            action = "Immediate inspection and drone survey required"
        elif near_sensitive:
            final_risk = "HIGH"
            action = "Manual inspection within 24 hours"
        else:
            final_risk = "HIGH"
            action = "Targeted satellite tasking recommended"
    
    elif numerical_risk_score >= 40 or base_risk == "MEDIUM":
        if very_close:
            final_risk = "HIGH"
            action = "Manual inspection within 48 hours"
        elif near_sensitive:
            final_risk = "MEDIUM"
            action = "Continue monitoring, drone survey if persists"
        else:
            final_risk = "MEDIUM"
            action = "Monitor with next satellite pass"
    
    else:  # LOW
        if very_close:
            final_risk = "MEDIUM"
            action = "Monitor closely due to proximity"
        else:
            final_risk = "LOW"
            action = "Normal monitoring schedule"
    
    # Build detailed response
    risk_details = {
        "risk_level": final_risk,
        "risk_score": round(numerical_risk_score, 2),
        "base_anomaly": base_risk,
        "recommended_action": action + persistence_note,
        "near_sensitive_zone": near_sensitive,
        "nearby_zones": nearby_zones,
        "closest_zone_distance_km": round(closest_distance, 2) if closest_distance != float('inf') else None,
        "persistent_anomaly": is_persistent,
        "seasonal_factor": round(seasonal_multiplier, 2),
        "indicator_severity": round(indicator_multiplier, 2)
    }
    
    # Add indicator-specific recommendations
    if indicators:
        risk_details["detected_indicators"] = indicators
        
        # Specific concerns based on indicators
        concerns = []
        for indicator in indicators:
            indicator_lower = indicator.lower()
            if "algal bloom" in indicator_lower:
                concerns.append("Potential harmful algal bloom - check oxygen levels and toxicity")
            elif "temperature" in indicator_lower:
                concerns.append("Thermal anomaly - monitor for coral stress and marine life impact")
            elif "reflectance" in indicator_lower:
                concerns.append("Surface change detected - check for oil spills, sediment plumes, or foam")
        
        if concerns:
            risk_details["specific_concerns"] = concerns
    
    return risk_details
