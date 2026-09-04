import React from 'react';
import { Mail, CheckCircle2, MousePointerClick, Reply, AlertTriangle, EyeOff, XCircle, Filter } from 'lucide-react';

export default function StatCards({ stats, activeFilter, onSelectFilter }) {
  if (!stats) return null;

  const cardConfig = [
    { key: 'ALL', label: 'Emails Detected', value: stats.emails_detected || 0, Icon: Mail, colorClass: 'text-slate-200', bgGlow: 'hover:border-slate-500/50' },
    { key: 'PROCESSED', label: 'Emails Processed', value: stats.emails_processed || 0, Icon: CheckCircle2, colorClass: 'text-indigo-400', bgGlow: 'hover:border-indigo-500/50 hover:shadow-indigo-500/10' },
    { key: 'CTA_FOUND', label: 'CTA Found', value: stats.cta_found || 0, Icon: MousePointerClick, colorClass: 'text-cyan-400', bgGlow: 'hover:border-cyan-500/50 hover:shadow-cyan-500/10' },
    { key: 'CTA_CLICKED', label: 'CTA Clicked', value: stats.cta_clicked || 0, Icon: MousePointerClick, colorClass: 'text-emerald-400', bgGlow: 'hover:border-emerald-500/50 hover:shadow-emerald-500/10' },
    { key: 'REPLIED', label: 'Replies Sent', value: stats.replies_sent || 0, Icon: Reply, colorClass: 'text-purple-400', bgGlow: 'hover:border-purple-500/50 hover:shadow-purple-500/10' },
    { key: 'CTA_BLOCKED', label: 'CTA Errors', value: stats.cta_errors || 0, Icon: AlertTriangle, colorClass: 'text-amber-400', bgGlow: 'hover:border-amber-500/50 hover:shadow-amber-500/10' },
    { key: 'ERROR', label: 'Reply Errors', value: stats.reply_errors || 0, Icon: XCircle, colorClass: 'text-rose-400', bgGlow: 'hover:border-rose-500/50 hover:shadow-rose-500/10' },
    { key: 'IGNORED', label: 'Ignored / Dupes', value: stats.ignored_emails || 0, Icon: EyeOff, colorClass: 'text-slate-400', bgGlow: 'hover:border-slate-600/50' },
  ];

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center px-1">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Metric Breakdown (Click card to filter table)</span>
        {activeFilter && activeFilter !== 'ALL' && (
          <button 
            onClick={() => onSelectFilter('ALL')} 
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20"
          >
            <Filter size={12} /> Reset Filter ({activeFilter})
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {cardConfig.map(({ key, label, value, Icon, colorClass, bgGlow }) => {
          const isActive = activeFilter === key;
          return (
            <div
              key={key}
              onClick={() => onSelectFilter(key === activeFilter ? 'ALL' : key)}
              className={`relative bg-slate-900/90 border p-3.5 rounded-xl space-y-2 cursor-pointer transition-all duration-300 transform hover:-translate-y-1 shadow-lg ${bgGlow} ${
                isActive 
                  ? 'border-indigo-500 ring-2 ring-indigo-500/40 bg-slate-800/90 shadow-indigo-500/20' 
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-center text-slate-400 text-[11px] font-medium">
                <span className="truncate max-w-[80px]">{label}</span>
                <Icon size={15} className={`${colorClass} transition-transform group-hover:scale-110`} />
              </div>
              <div className="flex items-baseline justify-between">
                <div className={`text-2xl font-bold tracking-tight ${colorClass}`}>
                  {value.toLocaleString()}
                </div>
                {isActive && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
