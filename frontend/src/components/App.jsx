import React, { useState } from 'react';
import Login from './Login';
import SignUp from './SignUp';
import AdminPanel from './AdminPanel';
import UserDashboard from './UserDashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAdmin, setIsAdmin] = useState(localStorage.getItem('isAdmin') === 'true');
  const [currentPage, setCurrentPage] = useState('login');

  const handleLogin = (token, admin) => {
    setToken(token);
    setIsAdmin(admin);
    localStorage.setItem('token', token);
    localStorage.setItem('isAdmin', admin);
    setCurrentPage(admin ? 'admin' : 'dashboard');
  };

  const handleSignUpSuccess = (token, admin) => {
    handleLogin(token, admin);
  };

  const handleLogout = () => {
    setToken(null);
    setIsAdmin(false);
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    setCurrentPage('login');
  };

  if (!token) {
    return (
      <div>
        {currentPage === 'login' && (
          <div>
            <Login onLogin={handleLogin} />
            <div style={{ 
              textAlign: 'center', 
              marginTop: '20px',
              fontSize: '16px',
              color: '#333'
            }}>
              <p>Don't have an account?{' '}
                <button 
                  onClick={() => setCurrentPage('signup')}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#667eea', 
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                >
                  Sign up here
                </button>
              </p>
            </div>
          </div>
        )}
        {currentPage === 'signup' && (
          <div>
            <SignUp onSignUpSuccess={handleSignUpSuccess} />
            <div style={{ 
              textAlign: 'center', 
              marginTop: '20px',
              fontSize: '16px',
              color: '#333'
            }}>
              <p>Already have an account?{' '}
                <button 
                  onClick={() => setCurrentPage('login')}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#667eea', 
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                >
                  Login here
                </button>
              </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <button 
        onClick={handleLogout} 
        style={{ 
          position: 'absolute', 
          top: '10px', 
          right: '10px',
          padding: '10px 20px',
          backgroundColor: '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        Logout
      </button>
      {isAdmin ? (
        <AdminPanel token={token} />
      ) : (
        <UserDashboard token={token} />
      )}
    </div>
  );
}

export default App;
