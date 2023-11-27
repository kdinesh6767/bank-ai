import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const AccountInput: React.FC = () => {
    const [accountNumber, setAccountNumber] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        try {
            // Replace with your FastAPI endpoint
            const response = await fetch("http://127.0.0.1:8000/accounts/validate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ account_number: accountNumber })
            });

            if (response.ok) {
                // Store accountNumber for future use, e.g., in local storage
                localStorage.setItem("accountNumber", accountNumber);
                navigate("/dashboard");
            } else {
                const errorResponse = await response.json();
                alert(errorResponse.detail || "Error validating account");
            }
        } catch (error) {
            console.error("Error validating account:", error);
            alert("Error validating account");
        }
    };

    //   const handleSubmit = async (event: React.FormEvent) => {
    //     event.preventDefault();
    //     try {
    //       // Replace with your validation endpoint
    //       const response = await fetch('http://127.0.0.1:8000/accounts/', {
    //         method: 'POST',
    //         headers: {
    //           'Content-Type': 'application/json',
    //         },
    //         body: JSON.stringify({ accountNumber }),
    //       });

    //       if (response.ok) {
    //         // Store accountNumber for future use, e.g., in local storage
    //         localStorage.setItem('accountNumber', accountNumber);
    //         navigate('/dashboard');
    //       } else {
    //         alert('Invalid account number');
    //       }
    //     } catch (error) {
    //       console.error('Error validating account number:', error);
    //       alert('Error validating account number');
    //     }
    //   };

    return (
        <div>
            <div className="background-overlay"></div>
            <div className="login-container">
                <h2 className="login-heading">Welcome to SelfBank</h2>
                <form onSubmit={handleSubmit} className="login-form">
                    <input
                        type="text"
                        className="login-input"
                        value={accountNumber}
                        onChange={e => setAccountNumber(e.target.value)}
                        placeholder="Enter Account Number"
                        required
                    />
                    <button type="submit" className="login-btn btn-grad">
                        Submit
                    </button>
                </form>
            </div>
        </div>
    );
};

export default AccountInput;
