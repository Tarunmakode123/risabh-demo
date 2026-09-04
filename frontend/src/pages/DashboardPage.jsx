import React, { useEffect, useState } from 'react';
import API from '../services/api';
import StatCards from '../components/StatCards';
import ActivityTable from '../components/ActivityTable';
import LogDetailModal from '../components/LogDetailModal';
import { RefreshCw, Radio, Download, Zap, ShieldCheck } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [isLive, setIsLive] = useState(true);

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
    if (!isLive) return;
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [isLive]);

  const handleExportCSV = () => {
    if (!activities || activities.length === 0) return;
    const headers = ['ID', 'Inbox', 'Sender', 'Subject', 'Status', 'Correlation ID', 'Time'];
    const rows = activities.map(a => [
      a.id,
      `"${a.inbox || ''}"`,
      `"${a.sender || ''}"`,
      `"${(a.subject || '').replace(/"/g, '""')}"`,
      a.status,
      a.correlation_id,
      a.created_at
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `arrowmail_activity_log_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-5 rounded-2xl border border-slate-800 shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight">Automation Command Center</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              LIVE POLLING
            </span>
          </div>
          <p className="text-slate-400 text-xs flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-indigo-400" />
            Real-time status for ArrowMail / GreenArrow test inbox interactions & CTA replies.
          </p>
        </div>

        {/* Header Quick Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition ${
              isLive 
                ? 'bg-slate-800/90 text-emerald-400 border-emerald-900/50 hover:bg-slate-800' 
                : 'bg-amber-950/60 text-amber-400 border-amber-800 hover:bg-amber-900/80'
            }`}
          >
            <Radio size={14} className={isLive ? 'animate-pulse' : ''} />
            {isLive ? 'Live Stream Active' : 'Stream Paused'}
          </button>

          <button
            onClick={handleExportCSV}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition shadow-sm"
            title="Export logs to CSV"
          >
            <Download size={14} />
            Export CSV
          </button>

          <button
            onClick={fetchData}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition shadow-lg shadow-indigo-600/20"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Sync Now
          </button>
        </div>
      </div>

      {/* Interactive Stat Cards Grid */}
      <StatCards 
        stats={stats} 
        activeFilter={activeFilter} 
        onSelectFilter={(f) => setActiveFilter(f)} 
      />

      {/* Activity Table Card Container */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-2xl backdrop-blur-xl">
        <div className="flex justify-between items-center pb-1 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-indigo-400 animate-pulse" />
            <h3 className="text-base font-bold text-slate-100">Live Interaction Stream</h3>
            {activeFilter !== 'ALL' && (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
                Filtered: {activeFilter}
              </span>
            )}
          </div>
          <span className="text-xs text-slate-500 font-mono flex items-center gap-1">
            <Radio size={12} className="text-emerald-400 animate-ping" /> Auto-updates every 4s
          </span>
        </div>

        <ActivityTable 
          activities={activities} 
          onSelectActivity={(act) => setSelectedActivity(act)}
          activeFilter={activeFilter}
          onSelectFilter={(f) => setActiveFilter(f)}
        />
      </div>

      {/* Interactive Log Detail Slide-Over Modal */}
      {selectedActivity && (
        <LogDetailModal 
          activity={selectedActivity} 
          onClose={() => setSelectedActivity(null)} 
        />
      )}
    </div>
  );
}
