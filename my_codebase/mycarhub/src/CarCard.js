import React from "react";
import { useNavigate } from "react-router-dom";
import imagePlaceholder from "./assets/imagePlaceholder.png";

function CarCard({ car }) {
  const navigate = useNavigate();

  let imageSrc = imagePlaceholder;
  if (car.images && car.images[0]) {
    try {
      imageSrc = require(`./assets/cars/${car.images[0]}`);
    } catch {
      imageSrc = imagePlaceholder;
    }
  }

  const isSold = car.status === "sold";

  return (
    <div style={{
      border: "1px solid #eee",
      borderRadius: 8,
      padding: 16,
      width: 260,
      boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
      background: "#fff",
      position: "relative"
    }}>
      <div style={{ position: "relative" }}>
        <img
          src={imageSrc}
          alt={car.productName}
          style={{
            width: "100%",
            height: 140,
            objectFit: "cover",
            borderRadius: 4,
            marginBottom: 12,
            filter: isSold ? "grayscale(0.7)" : "none",
            opacity: isSold ? 0.7 : 1
          }}
          onError={e => { e.target.src = imagePlaceholder; }}
        />
        {isSold && (
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: 140,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(255,255,255,0.7)",
            borderRadius: 4,
            fontWeight: "bold",
            fontSize: 28,
            color: "#d32f2f",
            letterSpacing: 2
          }}>
            SOLD
          </div>
        )}
      </div>
      <h3 style={{ margin: "8px 0" }}>{car.productName}</h3>
      <div style={{
        fontSize: 16,
        color: "#1976d2",
        fontWeight: "bold",
        marginBottom: 8,
        textDecoration: isSold ? "line-through" : "none",
        opacity: isSold ? 0.6 : 1
      }}>
        ${car.price?.toLocaleString() || "N/A"}
      </div>
      <div style={{ fontSize: 14, color: "#555" }}>{car.description}</div>
      <div style={{ fontSize: 13, color: "#888", margin: "8px 0" }}>
        <b>Year:</b> {car.year} <br />
        <b>Make:</b> {car.make} <br />
        <b>Miles:</b> {car.milesRun} <br />
        <b>Model #:</b> {car.modelNumber}
      </div>
      <div style={{ fontSize: 13 }}>
        <b>Features:</b>
        <ul>
          {car.features && car.features.map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </div>
      <div style={{ fontSize: 16, color: isSold ? "gray" : "#1976d2", fontWeight: "bold", marginBottom: 8,  opacity: isSold ? 0.6 : 1 }}>
        <b>Status:</b> {car.status} <br />
      </div>
      <button
        style={{
          marginTop: 12,
          padding: "8px 16px",
          background: "#1976d2",
          color: "#fff",
          border: "none",
          borderRadius: 4,
          cursor: "pointer",
          fontWeight: "bold",
          position: "relative",
          bottom: 4,
          opacity: isSold ? 0.6 : 1
        }}
        onClick={() => navigate(`/car-details/${car.id}`, { state: { car } })}
        disabled={isSold}
      >
        More
      </button>
    </div>
  );
}

export default CarCard;