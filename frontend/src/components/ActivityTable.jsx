import React, { useState } from 'react';
import { Search, Filter, CheckCircle2, Clock, AlertTriangle, XCircle, ArrowUpRight, Eye, RefreshCw } from 'lucide-react';

export default function ActivityTable({ activities, onSelectActivity, activeFilter, onSelectFilter }) {
  const [searchTerm, setSearchTerm] = useState('');

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-900/40 rounded-xl border border-slate-800/80 space-y-3">
        <Clock className="mx-auto h-8 w-8 text-slate-500 animate-pulse" />
        <p className="text-slate-400 text-sm font-medium">Waiting for incoming email interactions...</p>
        <p className="text-slate-500 text-xs">Emails sent to connected test inboxes will stream here in real time.</p>
      </div>
    );
  }

  // Filtering logic
  const filteredActivities = activities.filter((act) => {
    // Stat Card filter
    if (activeFilter && activeFilter !== 'ALL') {
      if (activeFilter === 'PROCESSED' && !['COMPLETED', 'REPLIED', 'CTA_CLICKED', 'CTA_VALIDATED'].includes(act.status)) return false;
      if (activeFilter === 'CTA_FOUND' && !['CTA_FOUND', 'CTA_VALIDATED', 'CTA_CLICKED', 'REPLIED', 'COMPLETED'].includes(act.status)) return false;
      if (activeFilter === 'CTA_CLICKED' && !['CTA_CLICKED', 'REPLIED', 'COMPLETED'].includes(act.status)) return false;
      if (activeFilter === 'REPLIED' && !['REPLIED', 'COMPLETED'].includes(act.status)) return false;
      if (activeFilter === 'CTA_BLOCKED' && act.status !== 'CTA_BLOCKED') return false;
      if (activeFilter === 'ERROR' && !['ERROR', 'FAILED'].includes(act.status)) return false;
      if (activeFilter === 'IGNORED' && !['IGNORED', 'DUPLICATE'].includes(act.status)) return false;
    }

    // Search filter
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (act.sender || '').toLowerCase().includes(term) ||
      (act.subject || '').toLowerCase().includes(term) ||
      (act.inbox || '').toLowerCase().includes(term) ||
      (act.status || '').toLowerCase().includes(term) ||
      (act.correlation_id || '').toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status) => {
    let style = 'bg-slate-800 text-slate-300 border-slate-700';
    let Icon = Clock;

    if (['COMPLETED', 'REPLIED'].includes(status)) {
      style = 'bg-purple-950/80 text-purple-300 border-purple-800/80 shadow-sm shadow-purple-900/30';
      Icon = CheckCircle2;
    } else if (['CTA_CLICKED', 'CTA_VALIDATED'].includes(status)) {
      style = 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80 shadow-sm shadow-emerald-900/30';
      Icon = CheckCircle2;
    } else if (['CTA_FOUND', 'PARSED'].includes(status)) {
      style = 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80';
      Icon = CheckCircle2;
    } else if (['CTA_BLOCKED', 'CTA_NOT_FOUND', 'IGNORED', 'DUPLICATE'].includes(status)) {
      style = 'bg-amber-950/80 text-amber-300 border-amber-800/80';
      Icon = AlertTriangle;
    } else if (['ERROR', 'FAILED'].includes(status)) {
      style = 'bg-rose-950/80 text-rose-300 border-rose-800/80';
      Icon = XCircle;
    }

    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${style}`}>
        <Icon size={12} />
        {status}
      </span>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Just now';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleString([], {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-3">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search activity by sender, subject, or correlation ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-slate-700/80 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
          />
        </div>

        {/* Status Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {['ALL', 'COMPLETED', 'CTA_CLICKED', 'CTA_BLOCKED', 'ERROR'].map((filterKey) => (
            <button
              key={filterKey}
              onClick={() => onSelectFilter(filterKey)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition border ${
                activeFilter === filterKey
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
                  : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {filterKey === 'ALL' ? 'Show All' : filterKey}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-900/60 shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-semibold text-[11px] tracking-wider">
            <tr>
              <th className="p-3.5 pl-4">Time</th>
              <th className="p-3.5">Inbox Account</th>
              <th className="p-3.5">Sender</th>
              <th className="p-3.5">Subject</th>
              <th className="p-3.5">Status</th>
              <th className="p-3.5 pr-4 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {filteredActivities.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-slate-500">
                  No matching activity logs found for your search/filter criteria.
                </td>
              </tr>
            ) : (
              filteredActivities.map((act) => (
                <tr
                  key={act.id}
                  onClick={() => onSelectActivity(act)}
                  className="group hover:bg-slate-800/80 transition-all duration-150 cursor-pointer"
                >
                  <td className="p-3.5 pl-4 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                    {formatDate(act.created_at || act.received_at)}
                  </td>
                  <td className="p-3.5 text-slate-200 font-medium whitespace-nowrap">
                    {act.inbox}
                  </td>
                  <td className="p-3.5 text-slate-300 max-w-xs truncate">
                    {act.sender}
                  </td>
                  <td className="p-3.5 text-slate-100 font-medium max-w-xs truncate group-hover:text-indigo-300 transition">
                    {act.subject}
                  </td>
                  <td className="p-3.5 whitespace-nowrap">
                    {getStatusBadge(act.status)}
                  </td>
                  <td className="p-3.5 pr-4 text-right whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 text-slate-400 group-hover:text-indigo-300 group-hover:bg-indigo-950/60 border border-slate-700/60 transition text-[11px]">
                      <Eye size={12} /> View
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
