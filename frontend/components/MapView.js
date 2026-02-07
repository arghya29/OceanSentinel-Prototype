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

export default function MapView({ data }) {
  const [icons, setIcons] = useState(null);

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

      setIcons({
        modelLow: square("#22c55e"),
        modelMedium: square("#f97316"),
        modelHigh: square("#dc2626"),
        modelCritical: square("#991b1b"),
        low: circle("#22c55e"),
        medium: circle("#f97316"),
      });
    });
  }, []);

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

  const realPoint = {
    lat: data.latitude,
    lng: data.longitude,
    risk: data.risk,
  };

  // FIXED: Observation points in OCEAN (EAST of Indian coast)
  const simulatedPoints = [
    { 
      lat: realPoint.lat + 0.15,
      lng: realPoint.lng + 0.35,
      risk: "LOW",
      source: "Coastal monitoring buoy"
    },
    { 
      lat: realPoint.lat - 0.15,
      lng: realPoint.lng + 0.45,
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

  const modelIcon = getModelIcon(realPoint.risk);

  return (
    <div style={{ position: "relative" }}>
      <MapContainer
        center={[realPoint.lat, realPoint.lng]}
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

        {/* MAIN DETECTION MARKER */}
        <Marker position={[realPoint.lat, realPoint.lng]} icon={modelIcon}>
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
                ♦ Detected Anomaly (Model Output)
              </div>
              
              <div style={{ marginBottom: "8px" }}>
                <strong style={{ color: "#475569" }}>Location:</strong> {data.locationName}
              </div>
              
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
        </div>
      </div>
    </div>
  );
}




