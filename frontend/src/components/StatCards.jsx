import React from 'react';
import { Mail, CheckCircle2, MousePointerClick, Reply, AlertTriangle, EyeOff, XCircle } from 'lucide-react';

export default function StatCards({ stats }) {
  if (!stats) return null;

  const card = (label, value, Icon, colorClass) => (
    <div className="bg-slate-800 border border-slate-700/70 p-4 rounded-xl space-y-2">
      <div className="flex justify-between items-center text-slate-400 text-xs font-medium">
        <span>{label}</span>
        <Icon size={16} className={colorClass} />
      </div>
      <div className={`text-2xl font-bold ${colorClass}`}>{value.toLocaleString()}</div>
    </div>
  );

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
      {card('Emails Detected', stats.emails_detected || 0, Mail, 'text-slate-200')}
      {card('Emails Processed', stats.emails_processed || 0, CheckCircle2, 'text-indigo-400')}
      {card('CTA Found', stats.cta_found || 0, MousePointerClick, 'text-cyan-400')}
      {card('CTA Clicked', stats.cta_clicked || 0, MousePointerClick, 'text-emerald-400')}
      {card('Replies Sent', stats.replies_sent || 0, Reply, 'text-purple-400')}
      {card('CTA Errors', stats.cta_errors || 0, AlertTriangle, 'text-amber-400')}
      {card('Reply Errors', stats.reply_errors || 0, XCircle, 'text-rose-400')}
      {card('Ignored / Dupes', stats.ignored_emails || 0, EyeOff, 'text-slate-400')}
    </div>
  );
}
