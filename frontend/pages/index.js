import { useEffect, useState } from "react";
import MapView from "../components/MapView";

/**
 * OceanSentinel Dashboard - DARK THEME VERSION
 * 
 * UPDATES:
 * 1. Support for separate region center and anomaly location coordinates
 * 2. Display distance from center to anomaly
 * 3. Show pixel coordinates for debugging
 * 4. Dark theme applied throughout
 */

export default function Home() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState("nellore");
  const [allLocations, setAllLocations] = useState([]);
  const [showImageModal, setShowImageModal] = useState(false);
  
  // Fetch available locations on mount
  useEffect(() => {
    fetch("http://localhost:5000/locations")
      .then(res => res.json())
      .then(data => {
        if (data.locations && Array.isArray(data.locations)) {
          const locationIds = data.locations.map(loc => loc.id);
          setAllLocations(locationIds);
        }
      })
      .catch(err => {
        console.error("Error fetching locations:", err);
        setAllLocations(["nellore", "bay_of_bengal_1", "chennai_coast"]);
      });
  }, []);

  // Fetch current location data
  useEffect(() => {
    setLoading(true);
    setError(null);
    
    fetch(`http://localhost:5000/analyze/${location}`)
      .then((res) => {
        if (!res.ok) throw new Error("Backend connection failed");
        return res.json();
      })
      .then((backendData) => {
        console.log("🔍 DEBUG - Backend response:", backendData);
        console.log("🔍 DEBUG - Region center:", backendData.location.region_center);
        console.log("🔍 DEBUG - Anomaly location:", backendData.detection.anomaly_location);
        
        const transformedData = {
          // Region center (for radar/scanning animation)
          regionCenter: {
            latitude: backendData.location.region_center.latitude,
            longitude: backendData.location.region_center.longitude
          },
          
          // Anomaly location (actual detected position)
          anomalyLocation: {
            latitude: backendData.detection.anomaly_location.latitude,
            longitude: backendData.detection.anomaly_location.longitude,
            distanceFromCenter: backendData.detection.anomaly_location.distance_from_center_km,
            pixelCoordinates: backendData.detection.anomaly_location.pixel_coordinates,
            normalizedCoordinates: backendData.detection.anomaly_location.normalized_coordinates
          },
          
          // Location info
          locationName: backendData.location.name,
          locationId: backendData.location.id,
          bbox: backendData.location.bbox,
          description: backendData.location.description,
          
          // Detection results
          anomaly: backendData.detection.anomaly_level,
          risk: backendData.risk_assessment.risk_level,
          score: backendData.detection.confidence_score,
          features: backendData.detection.features,
          indicators: backendData.indicators,
          
          // Risk assessment
          riskAssessment: {
            action: backendData.risk_assessment.recommended_action,
            nearSensitive: backendData.risk_assessment.near_sensitive_zone,
            nearbyZones: backendData.risk_assessment.nearby_zones || [],
            closestDistance: backendData.risk_assessment.closest_zone_distance_km,
            specificConcern: backendData.risk_assessment.specific_concern || null,
            persistentAnomaly: backendData.risk_assessment.persistent_anomaly || false,
            seasonalFactor: backendData.risk_assessment.seasonal_factor || 1.0,
            indicatorSeverity: backendData.risk_assessment.indicator_severity || 1.0,
            riskScore: backendData.risk_assessment.risk_score || null
          },
          
          // Satellite data
          satellite: {
            source: backendData.satellite_data.source,
            processingLevel: backendData.satellite_data.processing_level,
            before_date: backendData.satellite_data.before_date,
            after_date: backendData.satellite_data.after_date,
            resolution: backendData.satellite_data.resolution,
            retrievalMethod: backendData.satellite_data.retrieval_method,
            locationDescription: backendData.satellite_data.location_description
          },
          
          timestamp: backendData.timestamp
        };
        
        console.log("✅ Transformed data ready");
        console.log("   Region center:", transformedData.regionCenter);
        console.log("   Anomaly location:", transformedData.anomalyLocation);
        console.log("   Distance:", transformedData.anomalyLocation.distanceFromCenter, "km");
        
        setData(transformedData);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching data:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [location]);


  const sendAlert = (alertType) => {
    if (!data) return;

    fetch("http://localhost:5000/send-alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        location: data.locationName,
        risk_level: data.risk,
        confidence: data.score,
        action: data.riskAssessment.action
      })
    })
      .then(res => res.json())
      .then(result => {
        if (result.status === "success") {
          if (alertType === "email") {
            alert(`✅ Email Alert Sent!\n\nLocation: ${data.locationName}\nRisk: ${data.risk}\nScore: ${data.score.toFixed(2)}`);
          } else if (alertType === "sms") {
            alert(`✅ SMS Alert Sent!\n\nMessage: "OceanSentinel: ${data.locationName} - Risk ${data.risk} detected"`);
          }
        }
      })
      .catch(err => alert("❌ Error sending alert: " + err));
  };

  const formatLocationName = (locId) => {
    return locId
      .replace(/_/g, " ")
      .split(" ")
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Helper function to check if risk is high or critical
  const isHighRisk = (risk) => {
    if (!risk) return false;
    const normalizedRisk = risk.toString().toUpperCase().trim();
    return normalizedRisk === "HIGH" || normalizedRisk === "CRITICAL";
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      background: "linear-gradient(to bottom, #0f172a, #1e293b)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }}>
      {/* COMPACT HEADER */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        color: "white",
        padding: "16px 24px",
        boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
        position: "sticky",
        top: 0,
        zIndex: 2000,
        borderBottom: "1px solid rgba(255,255,255,0.1)"
      }}>
        <div style={{
          maxWidth: "1600px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "24px" }}>🌊</span>
            <h1 style={{ margin: 0, fontSize: "24px", fontWeight: "700" }}>
              OceanSentinel
            </h1>
            <span style={{ 
              fontSize: "12px", 
              background: "rgba(255,255,255,0.15)", 
              padding: "4px 8px", 
              borderRadius: "4px",
              fontWeight: "500"
            }}>
              Live Monitoring
            </span>
            <span style={{
              fontSize: "11px",
              background: "rgba(34, 197, 94, 0.2)",
              color: "#22c55e",
              padding: "4px 8px",
              borderRadius: "4px",
              fontWeight: "600",
              marginLeft: "8px"
            }}>
              🛰️ Real Sentinel-2 Data
            </span>
          </div>
          
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label style={{ fontSize: "14px", fontWeight: "500", opacity: 0.9 }}>
                📍 Location:
              </label>
              <select 
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{
                  padding: "8px 14px",
                  fontSize: "14px",
                  borderRadius: "8px",
                  border: "1px solid rgba(255,255,255,0.2)",
                  background: "rgba(255,255,255,0.1)",
                  color: "white",
                  fontWeight: "500",
                  cursor: "pointer",
                  outline: "none"
                }}
              >
                {allLocations.map(loc => (
                  <option key={loc} value={loc} style={{ background: "#1e293b", color: "white" }}>
                    {formatLocationName(loc)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ 
        maxWidth: "1600px", 
        margin: "0 auto", 
        padding: "24px",
        display: "grid",
        gridTemplateColumns: "1fr 400px",
        gap: "24px"
      }}>
        {/* LEFT COLUMN - MAP + SATELLITE DATA */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* MAP */}
          <div>
            {loading ? (
              <div style={{
                height: "600px",
                background: "rgba(30, 41, 59, 0.5)",
                borderRadius: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "16px",
                color: "#94a3b8",
                border: "1px solid rgba(255,255,255,0.1)"
              }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔄</div>
                  <div>Loading detection data...</div>
                </div>
              </div>
            ) : error ? (
              <div style={{
                height: "600px",
                background: "rgba(30, 41, 59, 0.5)",
                borderRadius: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "16px",
                color: "#ef4444",
                border: "1px solid rgba(239, 68, 68, 0.3)"
              }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
                  <div>Error: {error}</div>
                  <div style={{ fontSize: "14px", marginTop: "8px", color: "#94a3b8" }}>
                    Make sure backend is running on port 5000
                  </div>
                </div>
              </div>
            ) : data ? (
              <MapView data={data} />
            ) : null}
          </div>

          {/* SATELLITE DATA INFO */}
          {data && (
            <div style={{
              background: "rgba(30, 41, 59, 0.5)",
              padding: "20px",
              borderRadius: "16px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.1)"
            }}>
              <div style={{
                fontSize: "16px",
                fontWeight: "700",
                color: "#f1f5f9",
                marginBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}>
                🛰️ Satellite Data
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", color: "#cbd5e1", fontSize: "14px" }}>
                <div>
                  <strong>Source:</strong> {data.satellite.source}
                </div>
                <div>
                  <strong>Resolution:</strong> {data.satellite.resolution}
                </div>
                <div>
                  <strong>Before:</strong> {data.satellite.before_date}
                </div>
                <div>
                  <strong>After:</strong> {data.satellite.after_date}
                </div>
                <div>
                  <strong>Processing:</strong> {data.satellite.processingLevel}
                </div>
              </div>

              {/* View Images Button */}
              <button
                onClick={() => setShowImageModal(true)}
                style={{
                  width: "100%",
                  marginTop: "16px",
                  padding: "12px",
                  background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                  color: "white",
                  border: "none",
                  borderRadius: "8px",
                  fontWeight: "600",
                  fontSize: "14px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)"
                }}
              >
                🛰️ View Satellite Images
              </button>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN - DETECTION DETAILS */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* HIGH RISK ALERT */}
          {data && isHighRisk(data.risk) && (
            <div style={{
              background: "linear-gradient(135deg, #dc2626 0%, #991b1b 100%)",
              color: "white",
              padding: "20px",
              borderRadius: "16px",
              boxShadow: "0 8px 24px rgba(220, 38, 38, 0.4)",
              border: "1px solid rgba(220, 38, 38, 0.5)"
            }}>
              <div style={{ 
                fontSize: "18px", 
                fontWeight: "700", 
                marginBottom: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <span>⚠️</span> HIGH RISK ALERT
              </div>
              
              <div style={{ marginBottom: "12px", lineHeight: "1.6" }}>
                A high-risk marine anomaly has been detected at <strong>{data.locationName}</strong>
              </div>
              
              {data.riskAssessment.persistentAnomaly && (
                <div style={{
                  background: "rgba(255,255,255,0.15)",
                  padding: "12px",
                  borderRadius: "8px",
                  marginBottom: "12px",
                  fontSize: "14px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px"
                }}>
                  <span>🔁</span>
                  <span><strong>Persistent Anomaly</strong> — Detected multiple times in past 3 days</span>
                </div>
              )}
              
              <div style={{ 
                fontSize: "14px", 
                fontWeight: "600", 
                marginBottom: "8px",
                opacity: 0.9
              }}>
                Action Required:
              </div>
              <div style={{ 
                fontSize: "14px", 
                lineHeight: "1.5",
                background: "rgba(255,255,255,0.1)",
                padding: "12px",
                borderRadius: "8px"
              }}>
                {data.riskAssessment.action}
              </div>
              
              <div style={{
                display: "flex",
                gap: "12px",
                marginTop: "16px"
              }}>
                <button
                  onClick={() => sendAlert("email")}
                  style={{
                    flex: 1,
                    padding: "12px",
                    background: "white",
                    color: "#dc2626",
                    border: "none",
                    borderRadius: "8px",
                    fontWeight: "600",
                    fontSize: "14px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  📧 Email Alert
                </button>
                <button
                  onClick={() => sendAlert("sms")}
                  style={{
                    flex: 1,
                    padding: "12px",
                    background: "rgba(255,255,255,0.2)",
                    color: "white",
                    border: "2px solid white",
                    borderRadius: "8px",
                    fontWeight: "600",
                    fontSize: "14px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  📱 SMS Alert
                </button>
              </div>
            </div>
          )}

          {/* DETECTION ANALYSIS */}
          {data && (
            <div style={{
              background: "rgba(30, 41, 59, 0.5)",
              padding: "20px",
              borderRadius: "16px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.1)"
            }}>
              <div style={{
                fontSize: "16px",
                fontWeight: "700",
                color: "#f1f5f9",
                marginBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                🔍 Detection Analysis
              </div>

              {/* Anomaly Level */}
              <div style={{ marginBottom: "12px" }}>
                <div style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "4px" }}>
                  Anomaly Level:
                </div>
                <div style={{
                  fontSize: "20px",
                  fontWeight: "700",
                  color: data.anomaly === "HIGH" ? "#ef4444" : 
                         data.anomaly === "MEDIUM" ? "#f59e0b" : "#22c55e"
                }}>
                  {data.anomaly}
                </div>
              </div>

              {/* Confidence */}
              <div style={{ marginBottom: "12px" }}>
                <div style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "4px" }}>
                  Confidence:
                </div>
                <div style={{ fontSize: "24px", fontWeight: "700", color: "#f1f5f9" }}>
                  {data.score.toFixed(2)}
                </div>
              </div>

              {/* Risk Score */}
              <div style={{
                background: "rgba(59, 130, 246, 0.1)",
                padding: "12px",
                borderRadius: "12px",
                marginBottom: "12px",
                border: "1px solid rgba(59, 130, 246, 0.2)"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <span>📊</span>
                  <span style={{ fontSize: "13px", fontWeight: "600", color: "#60a5fa" }}>
                    Risk Score: {data.riskAssessment.riskScore}/100
                  </span>
                </div>
                <div style={{ fontSize: "12px", color: "#93c5fd" }}>
                  <div>🌊 Seasonal factor: {data.riskAssessment.seasonalFactor}x</div>
                  {data.anomalyLocation.distanceFromCenter > 0 && (
                    <div>📏 Distance from center: {data.anomalyLocation.distanceFromCenter.toFixed(2)} km</div>
                  )}
                </div>
              </div>

              {/* Detected Indicators */}
              <div style={{ marginTop: "16px" }}>
                <div style={{
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "#f1f5f9",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px"
                }}>
                  DETECTED INDICATORS:
                </div>
                <ul style={{
                  margin: 0,
                  padding: "0 0 0 20px",
                  fontSize: "13px",
                  color: "#cbd5e1",
                  lineHeight: "1.8"
                }}>
                  {data.indicators.map((indicator, i) => (
                    <li key={i}>{indicator}</li>
                  ))}
                </ul>
              </div>

              {/* Spatial Location Info */}
              {data.anomalyLocation.distanceFromCenter > 0 && (
                <div style={{
                  marginTop: "16px",
                  padding: "12px",
                  background: "rgba(245, 158, 11, 0.1)",
                  borderRadius: "8px",
                  fontSize: "12px",
                  border: "1px solid rgba(245, 158, 11, 0.2)"
                }}>
                  <div style={{ fontWeight: "600", color: "#fbbf24", marginBottom: "6px" }}>
                    📍 Spatial Analysis
                  </div>
                  <div style={{ color: "#fcd34d", lineHeight: "1.6" }}>
                    Anomaly detected <strong>{data.anomalyLocation.distanceFromCenter.toFixed(2)} km</strong> from monitoring region center
                    <br />
                    Position: {data.anomalyLocation.latitude.toFixed(4)}°N, {data.anomalyLocation.longitude.toFixed(4)}°E
                  </div>
                </div>
              )}

              {/* View Images Button */}
              <button
                onClick={() => setShowImageModal(true)}
                style={{
                  width: "100%",
                  marginTop: "16px",
                  padding: "12px",
                  background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                  color: "white",
                  border: "none",
                  borderRadius: "8px",
                  fontWeight: "600",
                  fontSize: "14px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)"
                }}
              >
                🛰️ View Satellite Images
              </button>
            </div>
          )}
        </div>
      </div>

      {/* IMAGE COMPARISON MODAL */}
      {data && showImageModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px"
          }}
          onClick={() => setShowImageModal(false)}
        >
          <div
            style={{
              background: "#1e293b",
              borderRadius: "16px",
              padding: "24px",
              maxWidth: "1200px",
              width: "100%",
              maxHeight: "90vh",
              overflow: "auto",
              position: "relative",
              border: "1px solid rgba(255,255,255,0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setShowImageModal(false)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: "#ef4444",
                color: "white",
                border: "none",
                borderRadius: "50%",
                width: "36px",
                height: "36px",
                fontSize: "20px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "bold",
                zIndex: 10
              }}
            >
              ×
            </button>

            {/* Title */}
            <h2 style={{
              margin: "0 0 20px 0",
              fontSize: "24px",
              fontWeight: "700",
              color: "#f1f5f9",
              textAlign: "center"
            }}>
              🛰️ Satellite Image Comparison
            </h2>

            <div style={{
              fontSize: "14px",
              color: "#94a3b8",
              textAlign: "center",
              marginBottom: "24px"
            }}>
              {data.locationName} • {data.satellite.before_date} vs {data.satellite.after_date}
            </div>

            {/* Image comparison grid */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "20px",
              marginBottom: "20px"
            }}>
              {/* Before Image */}
              <div>
                <div style={{
                  background: "rgba(59, 130, 246, 0.2)",
                  padding: "8px 12px",
                  borderRadius: "8px 8px 0 0",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#60a5fa",
                  textAlign: "center",
                  border: "1px solid rgba(59, 130, 246, 0.3)",
                  borderBottom: "none"
                }}>
                  📅 BEFORE: {data.satellite.before_date}
                </div>
                <div style={{
                  border: "2px solid #3b82f6",
                  borderRadius: "0 0 8px 8px",
                  overflow: "hidden",
                  background: "#0f172a",
                  aspectRatio: "1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <img
                    src={`http://localhost:5000/images/${location}_before.jpg`}
                    alt="Before satellite image"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover"
                    }}
                    onError={(e) => {
                      e.target.style.display = "none";
                      e.target.parentElement.innerHTML = '<div style="padding: 40px; text-align: center; color: #94a3b8;"><div style="font-size: 48px; margin-bottom: 12px;">🛰️</div><div>Satellite image not available</div></div>';
                    }}
                  />
                </div>
              </div>

              {/* After Image */}
              <div>
                <div style={{
                  background: "rgba(245, 158, 11, 0.2)",
                  padding: "8px 12px",
                  borderRadius: "8px 8px 0 0",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#fbbf24",
                  textAlign: "center",
                  border: "1px solid rgba(245, 158, 11, 0.3)",
                  borderBottom: "none"
                }}>
                  📅 AFTER: {data.satellite.after_date}
                </div>
                <div style={{
                  border: "2px solid #f59e0b",
                  borderRadius: "0 0 8px 8px",
                  overflow: "hidden",
                  background: "#0f172a",
                  aspectRatio: "1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <img
                    src={`http://localhost:5000/images/${location}_after.jpg`}
                    alt="After satellite image"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover"
                    }}
                    onError={(e) => {
                      e.target.style.display = "none";
                      e.target.parentElement.innerHTML = '<div style="padding: 40px; text-align: center; color: #94a3b8;"><div style="font-size: 48px; margin-bottom: 12px;">🛰️</div><div>Satellite image not available</div></div>';
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Detection Summary */}
            <div style={{
              background: "rgba(59, 130, 246, 0.1)",
              padding: "16px",
              borderRadius: "12px",
              border: "1px solid rgba(59, 130, 246, 0.3)"
            }}>
              <div style={{
                fontSize: "14px",
                fontWeight: "600",
                color: "#60a5fa",
                marginBottom: "8px"
              }}>
                🔍 Detection Summary
              </div>
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: "12px",
                fontSize: "13px",
                color: "#93c5fd"
              }}>
                <div>
                  <strong>Anomaly Level:</strong> {data.anomaly}
                </div>
                <div>
                  <strong>Risk Level:</strong> {data.risk}
                </div>
                <div>
                  <strong>Confidence:</strong> {data.score.toFixed(2)}
                </div>
                <div style={{ gridColumn: "1 / -1" }}>
                  <strong>Anomaly Position:</strong> {data.anomalyLocation.latitude.toFixed(4)}°N, {data.anomalyLocation.longitude.toFixed(4)}°E
                  ({data.anomalyLocation.distanceFromCenter.toFixed(2)} km from center)
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <footer style={{
        background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
        color: "rgba(255, 255, 255, 0.8)",
        padding: "12px 24px",
        fontSize: "13px",
        textAlign: "center",
        borderTop: "1px solid rgba(255, 255, 255, 0.1)",
        boxShadow: "0 -2px 8px rgba(0, 0, 0, 0.3)"
      }}>
        <div style={{
          maxWidth: "1600px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: "16px"
        }}>
          <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            🛰️ <strong style={{ color: "white" }}>OceanSentinel</strong>
          </span>
          <span style={{ color: "rgba(255, 255, 255, 0.3)" }}>•</span>
          <span>Real Sentinel-2 L2A Data via Sentinel Hub API</span>
          <span style={{ color: "rgba(255, 255, 255, 0.3)" }}>•</span>
          <span>ML-based anomaly detection</span>
          <span style={{ color: "rgba(255, 255, 255, 0.3)" }}>•</span>
          <span style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            color: "#22c55e",
            fontWeight: "600"
          }}>
            <span style={{
              width: "8px",
              height: "8px",
              background: "#22c55e",
              borderRadius: "50%",
              display: "inline-block",
              animation: "pulse 2s infinite"
            }}></span>
            Monitoring Active
          </span>
        </div>
        
        {/* Pulse animation */}
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}</style>
      </footer>
    </div>
  );
}