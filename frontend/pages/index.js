import { useEffect, useState } from "react";
import MapView from "../components/MapView";

/**
 * OceanSentinel Dashboard - Optimized Layout
 * 
 * Changes:
 * - HIGH RISK alert moved to right side panel
 * - Risk Assessment panel removed (redundant with map popup)
 * - Map gets full vertical space
 * - Cleaner, more focused layout
 * 
 * FIXED:
 * - Location dropdown now shows proper names (not 0, 1, 2)
 * - Correctly parses location array from backend
 */

export default function Home() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState("nellore");
  const [allLocations, setAllLocations] = useState([]);
  
  // Fetch available locations on mount
  useEffect(() => {
    fetch("http://localhost:5000/locations")
      .then(res => res.json())
      .then(data => {
        // FIXED: data.locations is an array, not an object
        // Extract the 'id' field from each location object
        if (data.locations && Array.isArray(data.locations)) {
          const locationIds = data.locations.map(loc => loc.id);
          setAllLocations(locationIds);
        }
      })
      .catch(err => {
        console.error("Error fetching locations:", err);
        // Fallback to default locations if API fails
        setAllLocations(["nellore", "bay_of_bengal_1", "chennai_coast"]);
      });
  }, []);

  // Fetch current location data
  useEffect(() => {
    setLoading(true);
    setError(null); // Clear previous errors
    
    fetch(`http://localhost:5000/analyze/${location}`)
      .then((res) => {
        if (!res.ok) throw new Error("Backend connection failed");
        return res.json();
      })
      .then((backendData) => {
        const transformedData = {
          latitude: backendData.location.latitude,
          longitude: backendData.location.longitude,
          locationName: backendData.location.name,
          locationId: backendData.location.id,
          anomaly: backendData.detection.anomaly_level,
          risk: backendData.risk_assessment.risk_level,
          score: backendData.detection.confidence_score,
          features: backendData.detection.features,
          indicators: backendData.indicators,
          riskAssessment: {
            action: backendData.risk_assessment.recommended_action,
            nearSensitive: backendData.risk_assessment.near_sensitive_zone,
            nearbyZones: backendData.risk_assessment.nearby_zones || [],
            closestDistance: backendData.risk_assessment.closest_zone_distance_km,
            specificConcern: backendData.risk_assessment.specific_concern || null,
            // NEW: Enhanced risk factors
            persistentAnomaly: backendData.risk_assessment.persistent_anomaly || false,
            seasonalFactor: backendData.risk_assessment.seasonal_factor || 1.0,
            indicatorSeverity: backendData.risk_assessment.indicator_severity || 1.0,
            riskScore: backendData.risk_assessment.risk_score || null
          },
          satellite: backendData.satellite_data,
          timestamp: backendData.timestamp
        };
        
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

  // Helper function to format location names
  const formatLocationName = (locId) => {
    return locId
      .replace(/_/g, " ")
      .split(" ")
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      background: "linear-gradient(to bottom, #f8fafc, #e2e8f0)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }}>
      {/* COMPACT HEADER */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        color: "white",
        padding: "16px 24px",
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        position: "sticky",
        top: 0,
        zIndex: 2000
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
          </div>
          
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label style={{ fontSize: "14px", fontWeight: "500", opacity: 0.9 }}>
                📍 Location:
              </label>
              <select 
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setLoading(true);
                }}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "2px solid rgba(255,255,255,0.2)",
                  fontSize: "14px",
                  fontWeight: "600",
                  cursor: "pointer",
                  background: "rgba(255,255,255,0.95)",
                  color: "#0f172a",
                  minWidth: "220px"
                }}
              >
                {allLocations.map(loc => (
                  <option key={loc} value={loc}>
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
        padding: "20px 24px"
      }}>
        {loading && !error && (
          <div style={{
            textAlign: "center",
            padding: "60px 20px",
            fontSize: "16px",
            color: "#64748b"
          }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🌊</div>
            Loading detection data...
          </div>
        )}

        {error && (
          <div style={{
            background: "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
            border: "2px solid #fca5a5",
            borderRadius: "12px",
            padding: "20px",
            textAlign: "center",
            color: "#991b1b",
            marginBottom: "20px"
          }}>
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>⚠️</div>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", fontWeight: "700" }}>
              Connection Error
            </h3>
            <p style={{ margin: 0, fontSize: "14px" }}>
              {error}
            </p>
            <p style={{ margin: "12px 0 0 0", fontSize: "13px", opacity: 0.8 }}>
              Make sure the backend is running on <code>http://localhost:5000</code>
            </p>
          </div>
        )}

        {!loading && !error && data && (
          <>
            {/* TWO-COLUMN LAYOUT */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 400px",
              gap: "20px",
              alignItems: "start"
            }}>
              {/* LEFT COLUMN - MAP AND FEATURES */}
              <div style={{
                display: "flex",
                flexDirection: "column",
                gap: "16px"
              }}>
                {/* Map Container */}
                <div style={{
                  background: "white",
                  borderRadius: "12px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  border: "1px solid #e2e8f0",
                  overflow: "hidden"
                }}>
                  <div style={{ position: "relative", zIndex: 1 }}>
                    <MapView data={data} />
                  </div>
                </div>

                {/* Features Summary */}
                <div style={{
                  background: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)",
                  borderRadius: "12px",
                  padding: "14px",
                  border: "1px solid #bae6fd",
                  fontSize: "12px"
                }}>
                  <div style={{ fontWeight: "600", marginBottom: "8px", color: "#0c4a6e" }}>
                    📊 Features Analyzed:
                  </div>
                  <div style={{ color: "#075985", lineHeight: "1.6" }}>
                    Mean Change: {data.features.mean_change.toFixed(2)} • 
                    Max Change: {data.features.max_change.toFixed(2)} • 
                    Significant Pixels: {data.features.significant_pixels_percent.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN - ALERTS & INFO */}
              <div style={{
                display: "flex",
                flexDirection: "column",
                gap: "16px"
              }}>
                {/* HIGH RISK ALERT (if applicable) */}
                {(data.risk === "HIGH" || data.risk === "CRITICAL") && (
                  <div style={{
                    background: "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)",
                    color: "white",
                    borderRadius: "12px",
                    padding: "18px",
                    boxShadow: "0 4px 12px rgba(220, 38, 38, 0.3)",
                    border: "2px solid #991b1b"
                  }}>
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      marginBottom: "12px"
                    }}>
                      <span style={{ fontSize: "28px" }}>⚠️</span>
                      <h3 style={{ margin: 0, fontSize: "18px", fontWeight: "700" }}>
                        {data.risk} RISK ALERT
                      </h3>
                    </div>
                    
                    <p style={{ 
                      margin: "0 0 12px 0", 
                      fontSize: "14px",
                      lineHeight: "1.5",
                      opacity: 0.95
                    }}>
                      A high-risk marine anomaly has been detected at <strong>{data.locationName}</strong>
                      {data.riskAssessment.persistentAnomaly && (
                        <span style={{ 
                          display: "block", 
                          marginTop: "6px",
                          padding: "6px 10px",
                          background: "rgba(0,0,0,0.2)",
                          borderRadius: "6px",
                          fontSize: "13px"
                        }}>
                          🔄 <strong>Persistent Anomaly</strong> - Detected multiple times in past 3 days
                        </span>
                      )}
                    </p>

                    <div style={{
                      background: "rgba(255,255,255,0.15)",
                      padding: "10px",
                      borderRadius: "8px",
                      marginBottom: "12px",
                      fontSize: "13px"
                    }}>
                      <div style={{ fontWeight: "600", marginBottom: "4px" }}>
                        Action Required:
                      </div>
                      <div style={{ lineHeight: "1.5" }}>
                        {data.riskAssessment.action}
                      </div>
                    </div>

                    <div style={{
                      display: "flex",
                      gap: "8px"
                    }}>
                      <button
                        onClick={() => sendAlert("email")}
                        style={{
                          flex: 1,
                          padding: "10px 16px",
                          background: "white",
                          color: "#dc2626",
                          border: "none",
                          borderRadius: "8px",
                          fontSize: "13px",
                          fontWeight: "600",
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
                          padding: "10px 16px",
                          background: "rgba(255,255,255,0.2)",
                          color: "white",
                          border: "1px solid white",
                          borderRadius: "8px",
                          fontSize: "13px",
                          fontWeight: "600",
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
                <div style={{
                  background: "white",
                  borderRadius: "12px",
                  padding: "18px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  border: "1px solid #e2e8f0"
                }}>
                  <h3 style={{ 
                    margin: "0 0 14px 0", 
                    fontSize: "16px", 
                    fontWeight: "700",
                    color: "#0f172a",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px"
                  }}>
                    🔍 Detection Analysis
                  </h3>
                  
                  <div style={{ fontSize: "14px", marginBottom: "12px" }}>
                    <div style={{ 
                      display: "flex", 
                      justifyContent: "space-between",
                      marginBottom: "8px",
                      paddingBottom: "8px",
                      borderBottom: "1px solid #e2e8f0"
                    }}>
                      <span style={{ color: "#64748b" }}>Anomaly Level:</span>
                      <span style={{ 
                        fontWeight: "700",
                        color: data.anomaly === "HIGH" ? "#dc2626" : 
                               data.anomaly === "MEDIUM" ? "#ea580c" : "#16a34a"
                      }}>
                        {data.anomaly}
                      </span>
                    </div>
                    
                    <div style={{ 
                      display: "flex", 
                      justifyContent: "space-between",
                      marginBottom: "12px"
                    }}>
                      <span style={{ color: "#64748b" }}>Confidence:</span>
                      <span style={{ fontWeight: "700", color: "#0f172a" }}>
                        {data.score.toFixed(2)}
                      </span>
                    </div>

                    {/* NEW: Enhanced Risk Factors */}
                    {data.riskAssessment.riskScore && (
                      <div style={{
                        background: "#f0f9ff",
                        padding: "10px",
                        borderRadius: "8px",
                        marginBottom: "12px",
                        fontSize: "13px"
                      }}>
                        <div style={{ fontWeight: "600", color: "#0c4a6e", marginBottom: "6px" }}>
                          📊 Risk Score: {data.riskAssessment.riskScore.toFixed(1)}/100
                        </div>
                        <div style={{ color: "#075985", fontSize: "12px", lineHeight: "1.5" }}>
                          {data.riskAssessment.seasonalFactor !== 1.0 && (
                            <div>🌦️ Seasonal factor: {data.riskAssessment.seasonalFactor.toFixed(2)}x</div>
                          )}
                          {data.riskAssessment.indicatorSeverity !== 1.0 && (
                            <div>⚠️ Indicator severity: {data.riskAssessment.indicatorSeverity.toFixed(2)}x</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div style={{ fontSize: "13px" }}>
                    <div style={{ 
                      fontWeight: "600", 
                      color: "#475569",
                      marginBottom: "8px"
                    }}>
                      DETECTED INDICATORS:
                    </div>
                    <ul style={{ 
                      margin: 0, 
                      paddingLeft: "20px", 
                      color: "#64748b",
                      lineHeight: "1.7"
                    }}>
                      {data.indicators.map((indicator, i) => (
                        <li key={i}>{indicator}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Satellite Data */}
                <div style={{
                  background: "white",
                  borderRadius: "12px",
                  padding: "16px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  border: "1px solid #e2e8f0"
                }}>
                  <h3 style={{ 
                    margin: "0 0 12px 0", 
                    fontSize: "15px", 
                    fontWeight: "700",
                    color: "#0f172a",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                  }}>
                    🛰️ Satellite Data
                  </h3>
                  <div style={{ fontSize: "13px", lineHeight: "1.8", color: "#475569" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span>Source:</span>
                      <span style={{ fontWeight: "600" }}>{data.satellite.source}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span>Resolution:</span>
                      <span style={{ fontWeight: "600" }}>{data.satellite.resolution}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span>Before:</span>
                      <span style={{ fontWeight: "600", fontSize: "12px" }}>{data.satellite.before_date}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>After:</span>
                      <span style={{ fontWeight: "600", fontSize: "12px" }}>{data.satellite.after_date}</span>
                    </div>
                  </div>
                </div>

                {/* Nearby Zones (if any) */}
                {data.riskAssessment.nearbyZones.length > 0 && (
                  <div style={{
                    background: "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)",
                    borderRadius: "12px",
                    padding: "14px",
                    border: "1px solid #fde68a",
                    fontSize: "12px"
                  }}>
                    <div style={{ fontWeight: "600", marginBottom: "8px", color: "#92400e" }}>
                      📍 Nearby Sensitive Zones:
                    </div>
                    <ul style={{ margin: "0", paddingLeft: "18px", color: "#78350f", lineHeight: "1.6" }}>
                      {data.riskAssessment.nearbyZones.slice(0, 2).map((zone, i) => (
                        <li key={i}>
                          {zone.name} ({zone.distance_km} km)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* FOOTER */}
            <div style={{
               marginTop: "16px",
               padding: "10px 16px",
               background: "#f1f5f9",
               borderTop: "1px solid #e2e8f0",
               fontSize: "12px",
               color: "#64748b",
               textAlign: "center"
           }}>
              🛰️ OceanSentinel Prototype • Sentinel-2 L2A • ML-based anomaly detection  
               &nbsp;•&nbsp;  
               <strong style={{ color: "#16a34a" }}>Monitoring Active</strong>
            </div>

          </>
        )}
      </div>
    </div>
  );
}