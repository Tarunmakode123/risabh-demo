import React, { useEffect, useState } from 'react';
import API from '../services/api';
import StatCards from '../components/StatCards';
import ActivityTable from '../components/ActivityTable';
import { RefreshCw, Play } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, actRes] = await Promise.all([
        API.get('/api/dashboard/stats'),
        API.get('/api/dashboard/activity')
      ]);
      setStats(statsRes.data);
      if (actRes.data && actRes.data.length > 0) {
        setActivities(actRes.data);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Automation Overview</h1>
          <p className="text-slate-400 text-xs">Real-time status for ArrowMail / GreenArrow test inbox interactions.</p>
        </div>
        <button
          onClick={fetchData}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium px-3.5 py-2 rounded-lg flex items-center gap-2"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Stats
        </button>
      </div>

      <StatCards stats={stats} />

      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4 shadow-lg">
        <div className="flex justify-between items-center">
          <h3 className="text-base font-semibold text-slate-100">Live Interaction Log Stream</h3>
          <span className="text-xs text-slate-500 font-mono">Auto-updates every 5s</span>
        </div>
        <ActivityTable activities={activities} />
      </div>
    </div>
  );
}
