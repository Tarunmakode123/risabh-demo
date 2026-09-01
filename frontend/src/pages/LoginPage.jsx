import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';
import { Flame, Lock, User } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const res = await API.post('/api/auth/token', formData);
      localStorage.setItem('token', res.data.access_token);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid login credentials');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 font-sans text-slate-100">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 w-full max-w-md space-y-6 shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex bg-indigo-600/20 p-3 rounded-2xl text-indigo-400">
            <Flame size={32} />
          </div>
          <h2 className="text-2xl font-bold">ArrowMail Automation</h2>
          <p className="text-slate-400 text-xs">Enter credentials to access the admin dashboard</p>
        </div>

        {error && (
          <div className="bg-rose-950 border border-rose-800 text-rose-300 p-3 rounded-lg text-xs text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 mb-1 font-medium">Username</label>
            <div className="relative">
              <User size={16} className="absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 mb-1 font-medium">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-xl transition shadow-lg text-sm mt-2"
          >
            Sign In to Dashboard
          </button>
        </form>
      </div>
    </div>
  );
}
