import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Flame, LayoutDashboard, Inbox, FileText, Settings as SettingsIcon, LogOut, Power, Menu, X } from 'lucide-react';

export default function Navbar({ isPaused, onTogglePause }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navItem = (path, label, Icon) => {
    const active = location.pathname === path;
    return (
      <Link
        to={path}
        onClick={() => setMobileOpen(false)}
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
    <nav className="bg-slate-900 border-b border-slate-800 px-4 sm:px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 md:space-x-6">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-base sm:text-lg">
            <Flame size={22} className="text-indigo-500" />
            <span className="truncate">ArrowMail Bot</span>
          </div>

          {/* Desktop Links */}
          <div className="hidden md:flex space-x-2">
            {navItem('/', 'Dashboard', LayoutDashboard)}
            {navItem('/inboxes', 'Inboxes', Inbox)}
            {navItem('/logs', 'Email Logs', FileText)}
            {navItem('/settings', 'Settings', SettingsIcon)}
          </div>
        </div>

        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Global Kill Switch Button */}
          <button
            onClick={onTogglePause}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold text-xs transition border ${
              isPaused
                ? 'bg-amber-950 text-amber-400 border-amber-800 hover:bg-amber-900'
                : 'bg-emerald-950 text-emerald-400 border-emerald-800 hover:bg-emerald-900'
            }`}
          >
            <Power size={13} />
            <span className="hidden sm:inline">{isPaused ? 'SYSTEM PAUSED' : 'SYSTEM ACTIVE'}</span>
            <span className="sm:hidden">{isPaused ? 'PAUSED' : 'ACTIVE'}</span>
          </button>

          <button
            onClick={handleLogout}
            className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg transition hidden sm:block"
            title="Logout"
          >
            <LogOut size={18} />
          </button>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-slate-400 hover:text-slate-200 p-1.5 rounded-lg"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileOpen && (
        <div className="md:hidden pt-3 pb-2 space-y-2 border-t border-slate-800 mt-3">
          {navItem('/', 'Dashboard', LayoutDashboard)}
          {navItem('/inboxes', 'Inboxes', Inbox)}
          {navItem('/logs', 'Email Logs', FileText)}
          {navItem('/settings', 'Settings', SettingsIcon)}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-sm text-rose-400 hover:bg-slate-800 transition"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}
