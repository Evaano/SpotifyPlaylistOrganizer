import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Analysis from "./components/Analysis";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-neutral-900 text-white font-sans selection:bg-green-500 selection:text-black">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analyze/:id" element={<Analysis />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
