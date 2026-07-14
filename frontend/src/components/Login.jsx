import React, { useState } from 'react';
import './Login.css';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('=== LOGIN ATTEMPT ===');
      
      // Step 1: Get token
      const response = await fetch('/api-token-auth/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const text = await response.text();
      if (!response.ok) { setError(`Login failed: ${response.status}`); setLoading(false); return; }

      const data = JSON.parse(text);
      const token = data.token;
      if (!token) { setError('No token'); setLoading(false); return; }

      console.log('Token received:', token);

      // Step 2: Check if admin
      console.log('Checking admin status...');
      const adminCheckResponse = await fetch('/api/user/admin-status/', {
        headers: { 'Authorization': `Token ${token}` }
      });

      if (!adminCheckResponse.ok) {
        console.warn('Could not check admin status, defaulting to regular user');
        onLogin(token, false);
        setLoading(false);
        return;
      }

      const adminData = await adminCheckResponse.json();
      const isAdmin = adminData.is_admin;

      console.log('Admin status:', isAdmin);
      console.log('✅ Login successful!');
      
      // Step 3: Login with actual admin status
      onLogin(token, isAdmin);
    } catch (err) {
      console.error('Login error:', err.message);
      setError(`Error: ${err.message}`);
    }

    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>💊 DermaCare</h1>
        <h2>Product Portfolio Manager</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input type="text" id="username" value={username}
              onChange={(e) => setUsername(e.target.value)} required />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input type="password" id="password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="login-button">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{ 
          textAlign: 'center', marginTop: '30px', fontSize: '14px',
          color: '#666', paddingTop: '20px', borderTop: '1px solid #ddd'
        }}>
          <p>Don't have an account?{' '}
            <a href="/signup" style={{ 
              color: '#667eea', textDecoration: 'underline',
              fontWeight: 'bold', cursor: 'pointer'
            }}>
              Sign up here
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
