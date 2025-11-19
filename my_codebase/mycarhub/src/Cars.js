import React from "react";
import CarCard from "./CarCard";

function Cars({ cars = [], selectedCategory }) {
  return (
    <main style={{ marginLeft: 290, padding: 24, width: "100%" }}>
      <h2>
        {selectedCategory ? `Cars in ${selectedCategory} category` : ""}
        {selectedCategory && (
          <span style={{ fontWeight: "normal", color: "#1976d2", marginLeft: 12 }}>
            ({selectedCategory})
          </span>
        )}
      </h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
        {cars.map((car, idx) => (
          <CarCard key={car.modelNumber || idx} car={car} selectedCategory={selectedCategory} />
        ))}
      </div>
    </main>
  );
}

export default Cars;