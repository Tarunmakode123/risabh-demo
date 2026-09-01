import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Flame, LayoutDashboard, Inbox, FileText, Settings as SettingsIcon, LogOut, Power } from 'lucide-react';

export default function Navbar({ isPaused, onTogglePause }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navItem = (path, label, Icon) => {
    const active = location.pathname === path;
    return (
      <Link
        to={path}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-sm transition ${
          active ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
        }`}
      >
        <Icon size={16} />
        {label}
      </Link>
    );
  };

  return (
    <nav class="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-6">
        <div className="flex items-center gap-2 text-indigo-400 font-bold text-lg">
          <Flame size={24} className="text-indigo-500" />
          <span>ArrowMail Automation</span>
        </div>
        <div className="flex space-x-2">
          {navItem('/', 'Dashboard', LayoutDashboard)}
          {navItem('/inboxes', 'Inboxes', Inbox)}
          {navItem('/logs', 'Email Logs', FileText)}
          {navItem('/settings', 'Settings', SettingsIcon)}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Global Kill Switch Button */}
        <button
          onClick={onTogglePause}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-semibold text-xs transition border ${
            isPaused
              ? 'bg-amber-950 text-amber-400 border-amber-800 hover:bg-amber-900'
              : 'bg-emerald-950 text-emerald-400 border-emerald-800 hover:bg-emerald-900'
          }`}
        >
          <Power size={14} />
          {isPaused ? 'SYSTEM PAUSED (Kill Switch)' : 'SYSTEM ACTIVE'}
        </button>

        <button
          onClick={handleLogout}
          className="text-slate-400 hover:text-rose-400 p-2 rounded-lg transition"
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </nav>
  );
}
