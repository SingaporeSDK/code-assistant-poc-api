import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import imagePlaceholder from "./assets/imagePlaceholder.png";
import ReviewBox from "./ReviewBox";

function CarDetails({ cars = [], onStatusChange }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const carFromState = location.state?.car;

  const [car, setCar] = useState(carFromState || null);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [isSold, setIsSold] = useState(carFromState?.status === "sold");
  const [showProcessing, setShowProcessing] = useState(false);
  const [transactionId, setTransactionId] = useState(null);

  useEffect(() => {
    if (carFromState) return;
    const found = cars.find(item => item.id === id);
    setCar(found || null);
    setIsSold(found?.status === "sold");
  }, [id, carFromState, cars]);

  const handlePurchase = async () => {
    setIsPurchasing(true);
    setShowProcessing(true);
    // Simulate payment processing delay
    setTimeout(async () => {
      setCar(prev => ({ ...prev, status: "sold" }));
      setIsSold(true);
      onStatusChange?.(id, "sold");
      // Generate a dummy transaction number
      setTransactionId("TXN-" + Math.floor(100000000 + Math.random() * 900000000));
      // Show "Processing payment" popup for 1 more second
      setTimeout(() => {
        setShowProcessing(false);
        setIsPurchasing(false);
      }, 1000);
    }, 2000);
  };

  const handleBack = () => {
    // If car was just purchased, trigger reload on back
    if (car.status === "sold") {
      navigate(-1, { state: { reload: true } });
    } else {
      navigate(-1);
    }
  };

  if (!car) return <div style={{ marginLeft: 290, padding: 24 }}>No car data found.</div>;

  const getImageSrc = (img) => {
    try {
      return require(`./assets/cars/${img}`);
    } catch {
      return imagePlaceholder;
    }
  };

  return (
    <main style={{ marginLeft: 290, padding: 24, width: "100%" }}>
      <button onClick={handleBack} style={{ marginBottom: 24 }}>Back</button>
      <h2>{car.productName}</h2>
      <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
        {(car.images && car.images.length > 0 ? car.images : [null]).map((img, idx) => (
          <img
            key={idx}
            src={img ? getImageSrc(img) : imagePlaceholder}
            alt={car.productName}
            style={{ width: 300, height: 200, objectFit: "cover", borderRadius: 8, background: "#eee" }}
            onError={e => { e.target.src = imagePlaceholder; }}
          />
        ))}
      </div>
      <div style={{ fontSize: 18, color: "#1976d2", fontWeight: "bold", margin: "16px 0", textDecoration: car.status === "sold" ? "line-through" : "none" }}>
        ${car.price?.toLocaleString() || "N/A"}
      </div>
      <div>{car.description}</div>
      <div style={{ margin: "16px 0" }}>
        <b>Year:</b> {car.year} <br />
        <b>Make:</b> {car.make} <br />
        <b>Miles:</b> {car.milesRun} <br />
        <b>Model #:</b> {car.modelNumber}
      </div>
      <div>
        <b>Features:</b>
        <ul>
          {car.features && car.features.map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </div>
      <div style={{ margin: "24px 0" }}>
        {car.status === "sold" ? (
          <span style={{ color: "red", fontWeight: "bold", fontSize: 18 }}>Status: Sold</span>
        ) : (
          <button
            onClick={handlePurchase}
            disabled={isPurchasing}
            style={{
              background: "#1976d2",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              padding: "12px 32px",
              fontWeight: "bold",
              fontSize: 18,
              cursor: isPurchasing ? "not-allowed" : "pointer"
            }}
          >
            {isPurchasing ? (
              <span>
                <span className="spinner" style={{
                  display: "inline-block",
                  width: 20,
                  height: 20,
                  border: "3px solid #fff",
                  borderTop: "3px solid #1976d2",
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite",
                  marginRight: 10,
                  verticalAlign: "middle"
                }} /> Processing...
              </span>
            ) : (
              "Purchase"
            )}
          </button>
        )}
      </div>
      {/* Transaction info after purchase */}
      {car.status === "sold" && transactionId && (
        <div style={{
          margin: "32px 0 0 0",
          padding: 24,
          background: "#e8f5e9",
          borderRadius: 8,
          border: "1px solid #b2dfdb",
          maxWidth: 500
        }}>
          <div style={{ fontWeight: "bold", marginBottom: 8 }}>
            Transaction Number: <span style={{ color: "#1976d2" }}>{transactionId}</span>
          </div>
          <div style={{ marginBottom: 8 }}>
            Please keep this transaction info for reference and reach out to our customer care at <b>+88 8888 8888</b> if you have any questions.
          </div>
          <div>
            An order confirmation email will be sent to you soon at the email provided in your profile.
          </div>
        </div>
      )}
      {showProcessing && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          background: "rgba(0,0,0,0.25)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 3000
        }}>
          <div style={{
            background: "#fff",
            padding: 40,
            borderRadius: 12,
            boxShadow: "0 2px 16px rgba(0,0,0,0.15)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center"
          }}>
            <div className="spinner" style={{
              width: 40,
              height: 40,
              border: "5px solid #1976d2",
              borderTop: "5px solid #eee",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              marginBottom: 20
            }} />
            <div style={{ fontSize: 20, fontWeight: "bold", color: "#1976d2" }}>
              Processing payment...
            </div>
          </div>
          <style>
            {`
              @keyframes spin {
                0% { transform: rotate(0deg);}
                100% { transform: rotate(360deg);}
              }
            `}
          </style>
        </div>
      )}
      {car.reviews && <ReviewBox reviews={car.reviews} />}
    </main>
  );
}

export default CarDetails;