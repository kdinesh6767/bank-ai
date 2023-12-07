import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import AccountInput from "./login";
import Dashboard from "./dashborad";
import "./style.css";

const App: React.FC = () => {
    return (
        <div className="main-container">
            <Router>
                <Routes>
                    <Route path="/" element={<AccountInput />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                </Routes>
            </Router>
        </div>
    );
};

export default App;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<App />);
