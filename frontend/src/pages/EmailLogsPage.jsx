import React, { useEffect, useState } from 'react';
import API from '../services/api';
import { RefreshCw, Filter } from 'lucide-react';

export default function EmailLogsPage() {
  const [emails, setEmails] = useState([]);
  const [filterStatus, setFilterStatus] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const url = filterStatus ? `/api/emails?status=${filterStatus}` : '/api/emails';
      const res = await API.get(url);
      if (res.data && res.data.length > 0) {
        setEmails(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, [filterStatus]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Processed Email Logs</h1>
          <p className="text-slate-400 text-xs">Complete audit trail of campaign email detection, CTA clicks, and threaded SMTP replies.</p>
        </div>
        <div className="flex gap-3">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="DETECTED">DETECTED</option>
            <option value="PARSED">PARSED</option>
            <option value="CTA_VALIDATED">CTA_VALIDATED</option>
            <option value="CTA_CLICKED">CTA_CLICKED</option>
            <option value="REPLIED">REPLIED</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="CTA_BLOCKED">CTA_BLOCKED</option>
            <option value="CTA_NOT_FOUND">CTA_NOT_FOUND</option>
            <option value="IGNORED">IGNORED</option>
            <option value="DUPLICATE">DUPLICATE</option>
            <option value="ERROR">ERROR</option>
          </select>

          <button onClick={fetchEmails} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium px-3.5 py-2 rounded-lg flex items-center gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700 uppercase">
              <tr>
                <th className="p-3">Received Time</th>
                <th className="p-3">Sender</th>
                <th className="p-3">Recipient</th>
                <th className="p-3">Subject</th>
                <th className="p-3">Message-ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Correlation ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 font-mono">
              {emails.length === 0 ? (
                <tr><td colSpan="7" className="p-8 text-center text-slate-500 font-sans">No matching email logs found.</td></tr>
              ) : (
                emails.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-750 font-sans">
                    <td className="p-3 text-slate-400 font-mono whitespace-nowrap">{e.created_at}</td>
                    <td className="p-3 text-slate-300 max-w-xs truncate">{e.sender}</td>
                    <td className="p-3 text-slate-400 max-w-xs truncate">{e.recipient}</td>
                    <td className="p-3 text-slate-100 max-w-xs truncate font-medium">{e.subject || '(No Subject)'}</td>
                    <td className="p-3 text-slate-400 font-mono truncate max-w-xs">{e.message_id}</td>
                    <td className="p-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-900 text-indigo-300 border border-slate-700">
                        {e.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-500 font-mono truncate max-w-xs">{e.correlation_id}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
