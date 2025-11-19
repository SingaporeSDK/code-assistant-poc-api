import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import Footer from "./Footer";
import Cars from "./Cars";
import CarDetails from "./CarDetails";
import LoginPage from "./LoginPage";
import AddCarPage from "./AddCarPage";
import { getInitialCars, normalizeNewCar } from "./services/localInventory";

function MainLayout() {
  const [cars, setCars] = useState(() => getInitialCars());
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Sedans");
  const [priceFilter, setPriceFilter] = useState({ min: "", max: "" });
  const [yearFilter, setYearFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  const handleCarStatusChange = (id, status) => {
    setCars(prev => prev.map(car => car.id === id ? { ...car, status } : car));
  };

  const handleAddCar = (newCar) => {
    const normalized = normalizeNewCar(newCar);
    setCars(prev => [normalized, ...prev]);
  };

  // Filter by category and search term
  const filteredCars = cars.filter(car =>
    (!selectedCategory || car.category === selectedCategory) &&
    (!statusFilter || car.status === statusFilter) &&
    (
      car.productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      car.modelNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      car.make.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Compute available years for dropdown
  const availableYears = Array.from(
    new Set(cars.map(car => car.year).filter(Boolean))
  ).sort((a, b) => b - a);

  // Filter cars based on price and year
  const finalFilteredCars = filteredCars.filter(car => {
    const min = priceFilter.min ? parseInt(priceFilter.min, 10) : -Infinity;
    const max = priceFilter.max ? parseInt(priceFilter.max, 10) : Infinity;
    const priceOk = car.price >= min && car.price <= max;
    const yearOk = yearFilter ? car.year === parseInt(yearFilter, 10) : true;
    return priceOk && yearOk;
  });

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    if (location.pathname !== "/cars") {
      navigate("/cars");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Header searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <div style={{ display: "flex", flex: 1 }}>
        {/* Hide Sidebar on /login route */}
        {location.pathname !== "/login" && (
          <Sidebar
            cars={cars}
            onCategorySelect={handleCategorySelect}
            selectedCategory={selectedCategory}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            priceFilter={priceFilter}
            setPriceFilter={setPriceFilter}
            yearFilter={yearFilter}
            setYearFilter={setYearFilter}
            availableYears={availableYears}
          />
        )}
        <Routes>
          <Route path="/cars" element={<Cars cars={finalFilteredCars} />} />
          <Route path="/car-details/:id" element={<CarDetails cars={cars} onStatusChange={handleCarStatusChange} />} />
          <Route path="*" element={<Cars cars={finalFilteredCars} />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/add-car" element={<AddCarPage onAddCar={handleAddCar} />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <MainLayout />
    </Router>
  );
}

export default App;
