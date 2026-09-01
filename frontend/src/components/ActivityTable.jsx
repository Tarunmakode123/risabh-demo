import React from 'react';

export default function ActivityTable({ activities }) {
  if (!activities || activities.length === 0) {
    return <div className="text-slate-500 text-center py-8">No recent email activities recorded yet.</div>;
  }

  const getStatusBadge = (status) => {
    let style = 'bg-slate-700 text-slate-300';
    if (['COMPLETED', 'REPLIED', 'CTA_CLICKED'].includes(status)) {
      style = 'bg-emerald-950 text-emerald-300 border border-emerald-800';
    } else if (['CTA_FOUND', 'CTA_VALIDATED', 'PARSED'].includes(status)) {
      style = 'bg-cyan-950 text-cyan-300 border border-cyan-800';
    } else if (['CTA_BLOCKED', 'CTA_NOT_FOUND', 'IGNORED', 'DUPLICATE'].includes(status)) {
      style = 'bg-amber-950 text-amber-300 border border-amber-800';
    } else if (['ERROR', 'FAILED'].includes(status)) {
      style = 'bg-rose-950 text-rose-300 border border-rose-800';
    }
    return <span className={`px-2.5 py-0.5 rounded text-xs font-semibold ${style}`}>{status}</span>;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700 text-xs uppercase font-semibold">
          <tr>
            <th className="p-3">Time</th>
            <th className="p-3">Inbox</th>
            <th className="p-3">Sender</th>
            <th className="p-3">Subject</th>
            <th className="p-3">Status</th>
            <th className="p-3">Correlation ID</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50">
          {activities.map((act) => (
            <tr key={act.id} className="hover:bg-slate-750 transition">
              <td className="p-3 text-slate-400 font-mono text-xs whitespace-nowrap">{act.created_at}</td>
              <td className="p-3 text-slate-200 font-medium whitespace-nowrap">{act.inbox}</td>
              <td className="p-3 text-slate-300 max-w-xs truncate">{act.sender}</td>
              <td className="p-3 text-slate-100 max-w-xs truncate">{act.subject}</td>
              <td className="p-3 whitespace-nowrap">{getStatusBadge(act.status)}</td>
              <td className="p-3 text-slate-500 font-mono text-xs truncate max-w-xs">{act.correlation_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
