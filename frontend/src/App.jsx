import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import API from './services/api';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import InboxesPage from './pages/InboxesPage';
import EmailLogsPage from './pages/EmailLogsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  const [isPaused, setIsPaused] = useState(false);

  const fetchSystemStatus = async () => {
    try {
      const res = await API.get('/api/system/status');
      setIsPaused(res.data.is_paused);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTogglePause = async () => {
    const endpoint = isPaused ? '/api/system/resume' : '/api/system/pause';
    await API.post(endpoint);
    fetchSystemStatus();
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
                <Navbar isPaused={isPaused} onTogglePause={handleTogglePause} />
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/inboxes" element={<InboxesPage />} />
                  <Route path="/logs" element={<EmailLogsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
