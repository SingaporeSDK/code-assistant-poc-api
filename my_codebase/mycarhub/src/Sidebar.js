import React, { useEffect, useState } from "react";

function Sidebar({
  cars = [],
  onCategorySelect,
  selectedCategory,
  statusFilter,
  setStatusFilter,
  ...props
}) {
  const categories = ["Sedans", "SUVs", "Trucks", "Hatchbacks", "Sports"];

  // Calculate counts from cars data
  const categoryCounts = categories.reduce((acc, cat) => {
    acc[cat] = cars.filter(car => car.category === cat).length;
    return acc;
  }, {});

  return (
    <aside className="Sidebar" style={{
      width: 250,
      height: "calc(100vh - 60px)",
      padding: 20,
      background: "white",
      boxShadow: "2px 0 8px rgba(0,0,0,0.07)",
      position: "fixed",
      overflowY: "auto",
      alignContent: "flex-start",
    }}>
      <h3>Categories</h3>
      <ul style={{ listStyleType: "none", padding: 0 }}>
        <li style={{ marginBottom: 16 }}>
          <button
            onClick={() => onCategorySelect("")}
            style={{
              background: "none",
              border: "none",
              color: !selectedCategory ? "#1976d2" : "#333",
              fontWeight: "bold",
              cursor: "pointer",
              fontSize: 16,
              padding: 0,
            }}
          >
            All Categories{" "}
            <span style={{ color: "#888", fontWeight: "normal" }}>
              ({cars.length})
            </span>
          </button>
        </li>
        {categories.map((category) => (
          <li key={category} style={{ marginBottom: 16 }}>
            <button
              onClick={() => onCategorySelect(category)}
              style={{
                background: "none",
                border: "none",
                color: selectedCategory === category ? "#1976d2" : "#333",
                fontWeight: "bold",
                cursor: "pointer",
                fontSize: 16,
                padding: 0,
              }}
            >
              {category}{" "}
              <span style={{ color: "#888", fontWeight: "normal" }}>
                ({categoryCounts[category] || 0})
              </span>
            </button>
          </li>
        ))}
      </ul>
      <hr style={{ margin: "20px 0" }} />
      <div>
        <h4>Filter by Status</h4>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ width: "100%", marginBottom: 16 }}
        >
          <option value="">All</option>
          <option value="available">Available</option>
          <option value="sold">Sold</option>
        </select>
      </div>
      <hr style={{ margin: "20px 0" }} />
      <div>
        <h4>Filter by Price</h4>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="number"
            placeholder="Min"
            value={props.priceFilter.min}
            onChange={e => props.setPriceFilter(f => ({ ...f, min: e.target.value }))}
            style={{ width: 60 }}
          />
          <span>-</span>
          <input
            type="number"
            placeholder="Max"
            value={props.priceFilter.max}
            onChange={e => props.setPriceFilter(f => ({ ...f, max: e.target.value }))}
            style={{ width: 60 }}
          />
        </div>
      </div>
      <hr style={{ margin: "20px 0" }} />
      <div>
        <h4>Filter by Year</h4>
        <select
          value={props.yearFilter}
          onChange={e => props.setYearFilter(e.target.value)}
          style={{ width: "100%" }}
        >
          <option value="">All Years</option>
          {props.availableYears.map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </div>
    </aside>
  );
}

export default Sidebar;
