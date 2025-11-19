import React from "react";
import { useNavigate } from "react-router-dom";
import carIcon from "../src/assets/cars/car.png"; // Adjust the path as necessary

function Header() {
  const navigate = useNavigate();

  return (
    <header
      className="Header"
      style={{
        background: "#f5f5f5",
        padding: "10px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        fontFamily: "Arial, sans-serif",
        position: "sticky",
        top: 0,
        zIndex: 1000,
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center" }}>
        <img
          src={carIcon}
          alt=""
          style={{ width: 40, height: 40, marginRight: 10 }}
        />
        <h2>My Car Hub</h2>
      </div>
      <div>
        <button
          style={{
            background: "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "8px 24px",
            fontWeight: "bold",
            fontSize: 16,
            cursor: "pointer",
          }}
          onClick={() => navigate("/login")}
        >
          Login
        </button>
      </div>
    </header>
  );
}

export default Header;