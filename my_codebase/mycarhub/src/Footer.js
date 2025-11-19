import React from "react";
import carIcon from "../src/assets/cars/car.png"; // Adjust the path as necessary


function Footer() {
  return (
    <footer className="Footer" style={{
      background: "#f5f5f5",
      padding: '10px',
      textAlign: 'center',
      fontFamily: 'Arial, sans-serif',
      position: 'fixed',
      bottom: 0,
      width: '100%',
      boxShadow: "0 -2px 4px rgba(0, 0, 0, 0.1)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center"
    }}>
      <div style={{ display: "flex", alignItems: "center" }}>
          <img
            src={carIcon}
            alt=""
            style={{ width: 40, height: 40, marginRight: 10 }}
          />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
          <span style={{ fontWeight: "bold", fontSize: 14, color: "#333" }}>My Car Hub</span>
          <div style={{ fontSize: 13, color: "#666" }}>Find your perfect car with confidence</div>
        </div>
        <div style={{ fontSize: 13, color: "#666", marginLeft: 24 }}>
          &copy; 2025 My Car Hub, all rights reserved.
        </div>
      </div>
    </footer>
  );
}

function App() {
  return (
    <div>
      <main style={{ marginLeft: 270, padding: 24, paddingBottom: 60, width: "100%" }}>
        {/* Your main content here */}
      </main>
      <Footer />
    </div>
  );
}

export default App;