import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function LoginPage() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    if (username === "admin" && password === "admin") {
      navigate("/add-car");
    } else {
      alert("Invalid credentials");
    }
  };

  return (
    <div style={{
      height: "100vh",
      width: "100vw",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f5f5f5",
      position: "fixed",
      top: 0,
      left: 0,
      zIndex: 2000
    }}>
      <div style={{
        background: "#fff",
        padding: 40,
        borderRadius: 12,
        boxShadow: "0 2px 16px rgba(0,0,0,0.10)",
        minWidth: 340,
        width: 360
      }}>
        <h2 style={{ textAlign: "center", marginBottom: 24 }}>Login</h2>
        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Username"
            style={{ padding: 12, fontSize: 16 }}
          />
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            style={{ padding: 12, fontSize: 16 }}
          />
          <button
            type="submit"
            style={{
              background: "#1976d2",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              padding: "12px 0",
              fontWeight: "bold",
              fontSize: 16,
              cursor: "pointer",
              marginTop: 10
            }}
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;