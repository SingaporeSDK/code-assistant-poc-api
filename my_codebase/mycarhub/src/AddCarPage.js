import React, { useState } from "react";

const initialCar = {
  modelNumber: "",
  productName: "",
  description: "",
  year: "",
  make: "",
  features: "",
  milesRun: "",
  price: "",
  images: "",
  status: "available",
  category: "Sedans"
};

const categories = ["Sedans", "SUVs", "Trucks", "Hatchbacks", "Sports"];

function AddCarPage({ onAddCar }) {
  const [car, setCar] = useState(initialCar);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCar(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const currentYear = new Date().getFullYear();
    if (parseInt(car.year, 10) < currentYear - 10) {
      alert(`Only cars from the last 10 years are allowed (Year >= ${currentYear - 10})`);
      return;
    }
    const carToSave = {
      ...car,
      year: parseInt(car.year, 10),
      milesRun: parseInt(car.milesRun, 10),
      price: parseFloat(car.price),
      features: car.features.split(",").map(f => f.trim()),
      images: car.images.split(",").map(f => f.trim())
    };
    if (onAddCar) {
      onAddCar(carToSave);
      alert("Car added locally!");
      setCar(initialCar);
    } else {
      alert("onAddCar handler is not configured.");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "40px auto", padding: 24, background: "#fff", borderRadius: 8 }}>
      <h2>Add New Car</h2>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <select name="category" value={car.category} onChange={handleChange} required>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <input name="modelNumber" value={car.modelNumber} onChange={handleChange} placeholder="Model Number" required />
        <input name="productName" value={car.productName} onChange={handleChange} placeholder="Product Name" required />
        <input name="description" value={car.description} onChange={handleChange} placeholder="Description" required />
        <input
          name="year"
          value={car.year}
          onChange={handleChange}
          placeholder="Year"
          type="number"
          min={new Date().getFullYear() - 10}
          max={new Date().getFullYear()}
          required
        />
        <input name="make" value={car.make} onChange={handleChange} placeholder="Make" required />
        <input name="features" value={car.features} onChange={handleChange} placeholder="Features (comma separated)" required />
        <input name="milesRun" value={car.milesRun} onChange={handleChange} placeholder="Miles Run" type="number" required />
        <input name="price" value={car.price} onChange={handleChange} placeholder="Price" type="number" required />
        <input name="images" value={car.images} onChange={handleChange} placeholder="Images (comma separated)" required />
        <select name="status" value={car.status} onChange={handleChange}>
          <option value="available">Available</option>
          <option value="sold">Sold</option>
        </select>
        <button
          type="submit"
          style={{
            background: "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "10px 0",
            fontWeight: "bold",
            fontSize: 16,
            cursor: "pointer"
          }}
        >
          Add Car
        </button>
      </form>
    </div>
  );
}

export default AddCarPage;