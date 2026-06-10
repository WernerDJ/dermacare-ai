import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import SignUp from './components/SignUp';
import AdminPanel from './components/AdminPanel';
import UserDashboard from './components/UserDashboard';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAdmin, setIsAdmin] = useState(localStorage.getItem('isAdmin') === 'true');
  const [currentPage, setCurrentPage] = useState(() => {
    if (window.location.pathname === '/signup') {
      return 'signup';
    }
    return 'login';
  });

  useEffect(() => {
    const handlePopState = () => {
      if (window.location.pathname === '/signup') {
        setCurrentPage('signup');
      } else {
        setCurrentPage('login');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleLogin = (token, admin) => {
    console.log('Login successful - Admin:', admin);
    setToken(token);
    setIsAdmin(admin);
    localStorage.setItem('token', token);
    localStorage.setItem('isAdmin', admin);
  };

  const handleSignUpSuccess = (token, admin) => {
    console.log('Signup successful - Admin:', admin);
    handleLogin(token, admin);
  };

  const handleLogout = () => {
    setToken(null);
    setIsAdmin(false);
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setCurrentPage('login');
    window.history.pushState(null, '', '/login');
  };

  if (!token) {
    return (
      <div>
        {currentPage === 'login' && <Login onLogin={handleLogin} />}
        {currentPage === 'signup' && <SignUp onSignUpSuccess={handleSignUpSuccess} />}
      </div>
    );
  }

  return (
    <div>
      <button 
        onClick={handleLogout} 
        style={{ 
          position: 'absolute', top: '10px', right: '10px',
          padding: '10px 20px', backgroundColor: '#667eea',
          color: 'white', border: 'none', borderRadius: '5px',
          cursor: 'pointer', fontSize: '14px'
        }}
      >
        Logout
      </button>
      {isAdmin ? (
        <AdminPanel token={token} onLogout={handleLogout} />
      ) : (
        <UserDashboard token={token} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;
