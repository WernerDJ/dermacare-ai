import React, { useState, useEffect } from 'react';
import { FiUpload, FiTrash2, FiLogOut, FiRefreshCw } from 'react-icons/fi';
import './AdminPanel.css';

function AdminPanel({ token, onLogout }) {
  const [portfolios, setPortfolios] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [brandName, setBrandName] = useState('');
  const [lookupIngredients, setLookupIngredients] = useState(true);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!token) return;  // Don't load if no token
    
    loadPortfolios();
    loadTasks();
    const interval = setInterval(loadTasks, 5000);
    return () => clearInterval(interval);
  }, [token]);  // Re-run when token changes
  const loadPortfolios = async () => {
    try {
      const response = await fetch('/api/portfolios/analysis_tasks/', {
        headers: { 'Authorization': `Token ${token}` }
      });
      const data = await response.json();
      setPortfolios(data);
    } catch (error) {
      console.error('Error loading portfolios:', error);
    }
  };

  const loadTasks = async () => {
    try {
      const response = await fetch('/api/portfolios/analysis_tasks/', {
        headers: { 'Authorization': `Token ${token}` }
      });
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();

    if (!selectedFile || !brandName) {
      alert('Please select a file and enter a brand name');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('pdf_file', selectedFile);
    formData.append('brand_name', brandName);
    formData.append('lookup_ingredients', lookupIngredients);

    try {
      const response = await fetch('/api/portfolios/upload_and_analyze/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Analysis started for ${brandName}. Task ID: ${data.task_id}`);
        setBrandName('');
        setSelectedFile(null);
        loadTasks();
      } else {
        alert('Error uploading file');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error uploading file');
    }
    setLoading(false);
  };

  const handleDelete = async (portfolioId) => {
    if (!window.confirm('Are you sure you want to delete this portfolio?')) {
      return;
    }

    try {
      const response = await fetch(`/api/portfolios/delete_portfolio/?portfolio_id=${portfolioId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Token ${token}` }
      });

      if (response.ok) {
        alert('Portfolio deleted');
        loadPortfolios();
      } else {
        alert('Error deleting portfolio');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error deleting portfolio');
    }
  };

  return (
    <div className="admin-container">
      <header className="admin-header">
        <h1>💊 DermaCare Admin Panel</h1>
        <button onClick={onLogout} className="logout-btn">
          <FiLogOut /> Logout
        </button>
      </header>

      <main className="admin-main">
        <section className="upload-section">
          <h2>📥 Analyze New Product Portfolio</h2>
          <form onSubmit={handleAnalyze} className="upload-form">
            <div className="form-group">
              <label htmlFor="brand-name">Brand Name</label>
              <input
                type="text"
                id="brand-name"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="e.g., Eucerin, Biotherm"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="pdf-file">PDF File</label>
              <input
                type="file"
                id="document-file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                required
              />
              {selectedFile && <p className="file-name">✅ {selectedFile.name}</p>}
            </div>

            <div className="form-group checkbox">
              <input
                type="checkbox"
                id="lookup-ingredients"
                checked={lookupIngredients}
                onChange={(e) => setLookupIngredients(e.target.checked)}
              />
              <label htmlFor="lookup-ingredients">🔍 Lookup Ingredients from APIs</label>
            </div>

            <button type="submit" disabled={loading} className="analyze-btn">
              {loading ? '⏳ Analyzing...' : '🚀 Analyze & Upload'}
            </button>
          </form>
        </section>

        <section className="tasks-section">
          <div className="section-header">
            <h2>⚙️ Analysis Tasks</h2>
            <button onClick={() => { setRefreshing(true); loadTasks(); setTimeout(() => setRefreshing(false), 1000); }} className="refresh-btn">
              <FiRefreshCw className={refreshing ? 'spinning' : ''} />
            </button>
          </div>

          {tasks.length === 0 ? (
            <p className="empty-message">No tasks yet</p>
          ) : (
            <div className="tasks-list">
              {tasks.map((task) => (
                <div key={task.id} className={`task-card task-${task.status}`}>
                  <div className="task-header">
                    <h3>{task.portfolio_name}</h3>
                    <span className={`status-badge ${task.status}`}>{task.status}</span>
                  </div>
                  <div className="task-content">
                    <p><strong>Step:</strong> {task.current_step || 'Initializing...'}</p>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${task.progress}%` }}></div>
                    </div>
                    <p className="progress-text">{task.progress}%</p>
                    {task.error_message && <p className="error-text">❌ {task.error_message}</p>}
                    <p className="task-date">{new Date(task.created_date).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="portfolios-section">
          <h2>📚 Saved Portfolios</h2>

          {portfolios.length === 0 ? (
            <p className="empty-message">No portfolios yet</p>
          ) : (
            <div className="portfolios-grid">
              {portfolios.map((portfolio) => (
                <div key={portfolio.id} className="portfolio-card">
                  <div className="portfolio-header">
                    <h3>{portfolio.portfolio_name}</h3>
                    <button
                      onClick={() => handleDelete(portfolio.id)}
                      className="delete-btn"
                      title="Delete portfolio"
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                  <div className="portfolio-info">
                    <p>📦 Products: <strong>{portfolio.total_products}</strong></p>
                    <p>🧪 With Ingredients: <strong>{portfolio.products_with_ingredients}</strong></p>
                    <p className="portfolio-date">
                      📅 {new Date(portfolio.created_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default AdminPanel;