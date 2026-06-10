import React, { useState, useEffect } from 'react';
import './UserDashboard.css';

function UserDashboard({ token, onLogout }) {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolios, setSelectedPortfolios] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [answering, setAnswering] = useState(false);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/portfolios/list_portfolios/', {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setPortfolios(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading portfolios:', error);
      setPortfolios([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePortfolioToggle = (portfolioId) => {
    setSelectedPortfolios(prev =>
      prev.includes(portfolioId) ? prev.filter(id => id !== portfolioId) : [...prev, portfolioId]
    );
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) { alert('Please enter a question'); return; }
    if (selectedPortfolios.length === 0) { alert('Please select at least one portfolio'); return; }

    try {
      setAnswering(true);
      const response = await fetch('/api/user-session/ask_question/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
        body: JSON.stringify({ question, brand_ids: selectedPortfolios })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setAnswer(data.answer || 'No answer received');
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setAnswering(false);
    }
  };

  if (loading) return <div className="dashboard-container"><h1>Loading portfolios...</h1></div>;

  return (
    <div className="dashboard-container">
      <h1>💊 DermaCare - User Dashboard</h1>
      <div className="dashboard-content">
        <div className="portfolios-section">
          <h2>Select Portfolios</h2>
          {portfolios.length === 0 ? (
            <p>No portfolios available</p>
          ) : (
            <div className="portfolios-list">
              {portfolios.map(portfolio => (
                <label key={portfolio.id} className="portfolio-item">
                  <input type="checkbox" checked={selectedPortfolios.includes(portfolio.id)} 
                    onChange={() => handlePortfolioToggle(portfolio.id)} />
                  <span>{portfolio.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="question-section">
          <h2>Ask a Question</h2>
          <form onSubmit={handleAskQuestion}>
            <textarea value={question} onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about the selected portfolios..." rows="4" />
            <button type="submit" disabled={answering}>
              {answering ? 'Thinking...' : 'Ask Question'}
            </button>
          </form>
          {answer && <div className="answer-section"><h3>Answer:</h3><p>{answer}</p></div>}
        </div>
      </div>
    </div>
  );
}

export default UserDashboard;
