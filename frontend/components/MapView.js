import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// React-Leaflet components (NO SSR)
const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false }
);
const Marker = dynamic(
  () => import("react-leaflet").then((m) => m.Marker),
  { ssr: false }
);
const Popup = dynamic(
  () => import("react-leaflet").then((m) => m.Popup),
  { ssr: false }
);
const Circle = dynamic(
  () => import("react-leaflet").then((m) => m.Circle),
  { ssr: false }
);
const Polyline = dynamic(
  () => import("react-leaflet").then((m) => m.Polyline),
  { ssr: false }
);

export default function MapView({ data }) {
  const [icons, setIcons] = useState(null);
  const [radarRadius, setRadarRadius] = useState(10000); // Start at 10km
  const [scanning, setScanning] = useState(true);

  // Create icons ONLY on client
  useEffect(() => {
    if (typeof window === "undefined") return;

    import("leaflet").then((L) => {
      const square = (color) =>
        new L.DivIcon({
          html: `<div style="
            width:20px;
            height:20px;
            background:${color};
            transform:rotate(45deg);
            border:2px solid white;
            box-shadow:0 0 8px rgba(0,0,0,0.4);
          "></div>`,
          className: "",
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

      const circle = (color) =>
        new L.DivIcon({
          html: `<div style="
            width:16px;
            height:16px;
            background:${color};
            border-radius:50%;
            border:2px solid white;
            box-shadow:0 0 8px rgba(0,0,0,0.4);
          "></div>`,
          className: "",
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });

      const centerMarker = () =>
        new L.DivIcon({
          html: `<div style="
            width:16px;
            height:16px;
            background:#3b82f6;
            border:3px solid white;
            border-radius:50%;
            box-shadow:0 0 12px rgba(59, 130, 246, 0.6);
          "></div>`,
          className: "",
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });

      setIcons({
        modelLow: square("#22c55e"),
        modelMedium: square("#f97316"),
        modelHigh: square("#dc2626"),
        modelCritical: square("#991b1b"),
        low: circle("#22c55e"),
        medium: circle("#f97316"),
        regionCenter: centerMarker(),
      });
    });
  }, []);

  // Animated radar scanning effect - CONTINUOUS, FULL AREA COVERAGE
  useEffect(() => {
    if (!scanning) return;

    const interval = setInterval(() => {
      setRadarRadius((prev) => {
        // Pulse from 10km to 45km (covers full 6500 km²), then reset
        if (prev >= 45000) {
          return 10000; // Reset to 10km
        }
        return prev + 1000; // Grow by 1km per step
      });
    }, 100); // Update every 100ms for smooth animation

    return () => {
      clearInterval(interval);
    };
  }, [scanning, data.locationName]); // Restart when location changes

  // Restart scanning when location changes
  useEffect(() => {
    setScanning(true);
    setRadarRadius(10000); // Reset to 10km
  }, [data.locationName]);

  if (!data || !icons) {
    return (
      <div style={{ 
        height: "600px", 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center",
        background: "#f3f4f6",
        color: "#64748b",
        fontSize: "14px"
      }}>
        Loading map...
      </div>
    );
  }

  // FIXED: Use separate coordinates
  const regionCenter = {
    lat: data.regionCenter.latitude,
    lng: data.regionCenter.longitude
  };

  const anomalyPoint = {
    lat: data.anomalyLocation.latitude,
    lng: data.anomalyLocation.longitude,
    risk: data.risk,
  };

  console.log("🗺️ MapView - Region center:", regionCenter);
  console.log("🗺️ MapView - Anomaly point:", anomalyPoint);
  console.log("🗺️ MapView - Distance:", data.anomalyLocation.distanceFromCenter, "km");

  // FIXED: Observation points in OCEAN (EAST of Indian coast)
  const simulatedPoints = [
    { 
      lat: anomalyPoint.lat + 0.15,
      lng: anomalyPoint.lng + 0.35,
      risk: "LOW",
      source: "Coastal monitoring buoy"
    },
    { 
      lat: anomalyPoint.lat - 0.15,
      lng: anomalyPoint.lng + 0.45,
      risk: "MEDIUM",
      source: "Offshore observation platform"
    },
  ];

  const getModelIcon = (risk) => {
    if (risk === "CRITICAL") return icons.modelCritical;
    if (risk === "HIGH") return icons.modelHigh;
    if (risk === "MEDIUM") return icons.modelMedium;
    return icons.modelLow;
  };

  const modelIcon = getModelIcon(anomalyPoint.risk);

  // Calculate area being analyzed
  const areaKm2 = Math.PI * Math.pow(radarRadius / 1000, 2);

  // Check if anomaly is at region center (within 0.5 km)
  const isAnomalyAtCenter = data.anomalyLocation.distanceFromCenter < 0.5;

  return (
    <div style={{ position: "relative" }}>
      <MapContainer
        center={[regionCenter.lat, regionCenter.lng]}
        zoom={8}
        style={{ 
          height: "600px", 
          width: "100%",
          zIndex: 1
         }}
      >
        <TileLayer 
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* ANIMATED RADAR SCANNING EFFECT - CENTERED ON REGION */}
        {scanning && (
          <>
            {/* Outer pulse ring */}
            <Circle
              center={[regionCenter.lat, regionCenter.lng]}
              radius={radarRadius}
              pathOptions={{
                color: "#3b82f6",
                fillColor: "#3b82f6",
                fillOpacity: 0.1,
                weight: 2,
                opacity: 0.6
              }}
            />
            
            {/* Inner bright ring */}
            <Circle
              center={[regionCenter.lat, regionCenter.lng]}
              radius={radarRadius * 0.8}
              pathOptions={{
                color: "#60a5fa",
                fillColor: "#60a5fa",
                fillOpacity: 0.15,
                weight: 1,
                opacity: 0.8
              }}
            />
          </>
        )}

        {/* Coverage area circle (always visible, subtle) - 6500 km² */}
        <Circle
          center={[regionCenter.lat, regionCenter.lng]}
          radius={45000} // 45km radius = ~6500 km² area
          pathOptions={{
            color: "#10b981",
            fillColor: "#10b981",
            fillOpacity: 0.05,
            weight: 1,
            opacity: 0.3,
            dashArray: "5, 5"
          }}
        />

        {/* REGION CENTER MARKER (scanning origin) */}
        {!isAnomalyAtCenter && (
          <Marker position={[regionCenter.lat, regionCenter.lng]} icon={icons.regionCenter}>
            <Popup maxWidth={280}>
              <div style={{ fontSize: "13px", lineHeight: "1.6" }}>
                <div style={{ 
                  fontSize: "15px", 
                  fontWeight: "700", 
                  color: "#3b82f6",
                  marginBottom: "8px",
                  paddingBottom: "8px",
                  borderBottom: "2px solid #e5e7eb"
                }}>
                  ● Monitoring Region Center
                </div>
                
                <div style={{ marginBottom: "6px" }}>
                  <strong>Location:</strong> {data.locationName}
                </div>
                
                <div style={{ marginBottom: "6px" }}>
                  <strong>Coordinates:</strong> {regionCenter.lat.toFixed(4)}°N, {regionCenter.lng.toFixed(4)}°E
                </div>
                
                <div style={{ 
                  fontSize: "12px",
                  color: "#64748b",
                  marginTop: "8px",
                  padding: "8px",
                  background: "#f8fafc",
                  borderRadius: "6px"
                }}>
                  This is the center of the satellite monitoring region (~6500 km²). 
                  The scanning animation radiates from this point.
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* LINE CONNECTING CENTER TO ANOMALY (if different) */}
        {!isAnomalyAtCenter && (
          <Polyline
            positions={[
              [regionCenter.lat, regionCenter.lng],
              [anomalyPoint.lat, anomalyPoint.lng]
            ]}
            pathOptions={{
              color: "#f97316",
              weight: 2,
              opacity: 0.6,
              dashArray: "10, 10"
            }}
          />
        )}

        {/* ANOMALY DETECTION MARKER */}
        <Marker position={[anomalyPoint.lat, anomalyPoint.lng]} icon={modelIcon}>
          <Popup maxWidth={320}>
            <div style={{ fontSize: "13px", lineHeight: "1.6" }}>
              <div style={{ 
                fontSize: "15px", 
                fontWeight: "700", 
                color: "#1e40af",
                marginBottom: "8px",
                paddingBottom: "8px",
                borderBottom: "2px solid #e5e7eb"
              }}>
                ♦ Detected Anomaly
              </div>
              
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ color: "#475569" }}>Location:</strong> {data.locationName}
              </div>
              
              {!isAnomalyAtCenter && (
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ color: "#475569" }}>Distance from center:</strong>{" "}
                  <span style={{ color: "#f97316", fontWeight: "600" }}>
                    {data.anomalyLocation.distanceFromCenter.toFixed(2)} km
                  </span>
                </div>
              )}
              
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ color: "#475569" }}>Risk Level:</strong>{" "}
                <span style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: "700",
                  background: data.risk === "HIGH" || data.risk === "CRITICAL" ? "#fee2e2" :
                             data.risk === "MEDIUM" ? "#ffedd5" : "#dcfce7",
                  color: data.risk === "HIGH" || data.risk === "CRITICAL" ? "#dc2626" :
                         data.risk === "MEDIUM" ? "#ea580c" : "#16a34a"
                }}>
                  {data.risk}
                </span>
              </div>
              
              <div style={{ 
                background: "#f8fafc", 
                padding: "8px", 
                borderRadius: "6px",
                marginBottom: "8px",
                fontSize: "12px"
              }}>
                <div style={{ marginBottom: "4px" }}>
                  <strong>Anomaly:</strong> {data.anomaly}
                </div>
                <div>
                  <strong>Confidence:</strong> {data.score.toFixed(2)}
                </div>
              </div>
              
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ fontSize: "12px", color: "#64748b" }}>Indicators:</strong>
                <ul style={{ 
                  margin: "4px 0 0 0", 
                  paddingLeft: "18px",
                  fontSize: "12px",
                  color: "#475569"
                }}>
                  {data.indicators.slice(0, 2).map((indicator, i) => (
                    <li key={i} style={{ marginBottom: "2px" }}>{indicator}</li>
                  ))}
                </ul>
              </div>
              
              {data.riskAssessment.nearbyZones.length > 0 && (
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ fontSize: "12px", color: "#64748b" }}>Nearby Zones:</strong>
                  <ul style={{ 
                    margin: "4px 0 0 0", 
                    paddingLeft: "18px",
                    fontSize: "12px",
                    color: "#475569"
                  }}>
                    {data.riskAssessment.nearbyZones.slice(0, 1).map((zone, i) => (
                      <li key={i}>
                        {zone.name} ({zone.distance_km} km)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div style={{
                background: "#fef3c7",
                padding: "8px",
                borderRadius: "6px",
                marginTop: "8px",
                fontSize: "12px",
                lineHeight: "1.5"
              }}>
                <strong style={{ color: "#92400e" }}>Action:</strong>
                <div style={{ color: "#78350f", marginTop: "4px" }}>
                  {data.riskAssessment.action}
                </div>
              </div>
            </div>
          </Popup>
        </Marker>

        {/* OBSERVATION POINTS */}
        {simulatedPoints.map((p, i) => (
          <Marker
            key={i}
            position={[p.lat, p.lng]}
            icon={p.risk === "LOW" ? icons.low : icons.medium}
          >
            <Popup>
              <div style={{ fontSize: "13px", lineHeight: "1.6" }}>
                <div style={{ 
                  fontSize: "14px", 
                  fontWeight: "700", 
                  color: "#1e40af",
                  marginBottom: "8px"
                }}>
                  ● Observation Point
                </div>
                <div style={{ marginBottom: "4px" }}>
                  <strong>Risk:</strong> {p.risk}
                </div>
                <div style={{ fontSize: "12px", color: "#64748b" }}>
                  <strong>Source:</strong> {p.source}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* MAP TITLE OVERLAY - TOP LEFT */}
      <div style={{
        position: "absolute",
        top: 16,
        left: 16,
        zIndex: 1000,
        background: "rgba(255,255,255,0.95)",
        padding: "12px 16px",
        borderRadius: "10px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(0,0,0,0.1)",
        maxWidth: "320px"
      }}>
        <div style={{ 
          fontSize: "15px", 
          fontWeight: "700",
          color: "#0f172a",
          marginBottom: "4px",
          display: "flex",
          alignItems: "center",
          gap: "8px"
        }}>
          🗺️ Real-Time Detection Map
        </div>
        <div style={{ 
          fontSize: "13px", 
          color: "#64748b"
        }}>
          Currently showing: <span style={{ fontWeight: "600", color: "#1e40af" }}>{data.locationName}</span>
        </div>
        
        {/* Scanning indicator - ALWAYS VISIBLE since continuous */}
        <div style={{
          marginTop: "8px",
          padding: "6px 10px",
          background: "#dbeafe",
          borderRadius: "6px",
          fontSize: "12px",
          color: "#1e40af",
          fontWeight: "600",
          display: "flex",
          alignItems: "center",
          gap: "6px"
        }}>
          <div style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#3b82f6",
            animation: "pulse 1s ease-in-out infinite"
          }}></div>
          Scanning area: {areaKm2.toFixed(1)} km² (Total: 6500 km²)
        </div>

        {/* Spatial info */}
        {!isAnomalyAtCenter && (
          <div style={{
            marginTop: "8px",
            padding: "6px 10px",
            background: "#fef3c7",
            borderRadius: "6px",
            fontSize: "11px",
            color: "#78350f",
            lineHeight: "1.4"
          }}>
            <strong>📏 Anomaly detected {data.anomalyLocation.distanceFromCenter.toFixed(2)} km from scan center</strong>
          </div>
        )}
      </div>

      {/* LEGEND - BOTTOM RIGHT */}
      <div style={{
        position: "absolute",
        bottom: 16,
        right: 16,
        zIndex: 1000,
        background: "rgba(255,255,255,0.95)",
        padding: "12px 14px",
        borderRadius: "10px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        backdropFilter: "blur(10px)",
        fontSize: "12px",
        border: "1px solid rgba(0,0,0,0.1)"
      }}>
        <div style={{ fontWeight: "700", marginBottom: "8px", color: "#0f172a" }}>
          Risk Levels
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#22c55e",
              border: "2px solid white",
              boxShadow: "0 0 4px rgba(0,0,0,0.2)"
            }}></div>
            <span style={{ color: "#475569" }}>Low — Normal</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#f97316",
              border: "2px solid white",
              boxShadow: "0 0 4px rgba(0,0,0,0.2)"
            }}></div>
            <span style={{ color: "#475569" }}>Medium — Monitor</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#dc2626",
              border: "2px solid white",
              boxShadow: "0 0 4px rgba(0,0,0,0.2)"
            }}></div>
            <span style={{ color: "#475569" }}>High — Inspection</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", paddingTop: "4px", borderTop: "1px solid #e5e7eb" }}>
            <div style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#3b82f6",
              border: "2px solid white",
              boxShadow: "0 0 4px rgba(0,0,0,0.2)"
            }}></div>
            <span style={{ color: "#475569" }}>Scan Center</span>
          </div>
        </div>
      </div>

      {/* CSS for pulse animation */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.2);
          }
        }
      `}</style>
    </div>
  );
}




