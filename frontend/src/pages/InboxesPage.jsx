import React, { useEffect, useState } from 'react';
import API from '../services/api';
import { Plus, Power, Trash2, Plug, CheckCircle2, AlertCircle } from 'lucide-react';

export default function InboxesPage() {
  const [accounts, setAccounts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    imap_host: 'imap.example.com',
    imap_port: 993,
    smtp_host: 'smtp.example.com',
    smtp_port: 587,
    use_ssl: true,
    folder: 'INBOX'
  });

  const fetchAccounts = async () => {
    try {
      const res = await API.get('/api/accounts');
      setAccounts(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      await API.post('/api/accounts', form);
      setShowModal(false);
      fetchAccounts();
    } catch (err) {
      alert('Error saving inbox account: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggle = async (id) => {
    await API.post(`/api/accounts/${id}/toggle`);
    fetchAccounts();
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this inbox account?')) return;
    await API.delete(`/api/accounts/${id}`);
    fetchAccounts();
  };

  const handleTestImap = async (id) => {
    setTestResult('Testing IMAP connection...');
    try {
      const res = await API.post(`/api/accounts/${id}/test-imap`);
      setTestResult(res.data.success ? '✓ IMAP Connection Successful!' : '✗ IMAP Failed: ' + res.data.message);
    } catch (err) {
      setTestResult('Error: ' + err.message);
    }
  };

  const handleTestSmtp = async (id) => {
    setTestResult('Testing SMTP connection...');
    try {
      const res = await API.post(`/api/accounts/${id}/test-smtp`);
      setTestResult(res.data.success ? '✓ SMTP Connection Successful!' : '✗ SMTP Failed: ' + res.data.message);
    } catch (err) {
      setTestResult('Error: ' + err.message);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Test Inbox Accounts</h1>
          <p className="text-slate-400 text-xs">Configure controlled test inboxes monitored via IMAP & SMTP.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Plus size={16} /> Add Test Inbox
        </button>
      </div>

      {testResult && (
        <div className="bg-slate-800 border border-indigo-500/50 p-3 rounded-lg text-xs text-indigo-300">
          {testResult}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {accounts.map((acc) => (
          <div key={acc.id} className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-3 shadow-lg flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-slate-100 truncate">{acc.email}</h3>
                  <p className="text-xs text-slate-400">User: {acc.username}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${acc.is_active ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-700 text-slate-400'}`}>
                  {acc.is_active ? 'Active' : 'Disabled'}
                </span>
              </div>

              <div className="text-xs text-slate-400 space-y-1 bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                <div><strong class="text-slate-300">IMAP:</strong> {acc.imap_host}:{acc.imap_port}</div>
                <div><strong class="text-slate-300">SMTP:</strong> {acc.smtp_host}:{acc.smtp_port}</div>
                <div><strong class="text-slate-300">Folder:</strong> {acc.folder}</div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-slate-700/60 text-xs">
              <div className="flex gap-2">
                <button onClick={() => handleTestImap(acc.id)} className="text-slate-300 hover:text-indigo-400 flex items-center gap-1">
                  <Plug size={12} /> Test IMAP
                </button>
                <button onClick={() => handleTestSmtp(acc.id)} className="text-slate-300 hover:text-purple-400 flex items-center gap-1">
                  <Plug size={12} /> Test SMTP
                </button>
              </div>

              <div className="flex gap-3">
                <button onClick={() => handleToggle(acc.id)} className="text-slate-400 hover:text-indigo-400">
                  <Power size={14} />
                </button>
                <button onClick={() => handleDelete(acc.id)} className="text-rose-400 hover:text-rose-300">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Inbox Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-lg space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-100">Add Controlled Test Inbox</h3>
            <form onSubmit={handleSave} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Email Address</label>
                <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Username</label>
                  <input required type="text" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Password / App Secret</label>
                  <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">IMAP Host</label>
                  <input required type="text" value={form.imap_host} onChange={(e) => setForm({ ...form, imap_host: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">IMAP Port</label>
                  <input required type="number" value={form.imap_port} onChange={(e) => setForm({ ...form, imap_port: parseInt(e.target.value) })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">SMTP Host</label>
                  <input required type="text" value={form.smtp_host} onChange={(e) => setForm({ ...form, smtp_host: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">SMTP Port</label>
                  <input required type="number" value={form.smtp_port} onChange={(e) => setForm({ ...form, smtp_port: parseInt(e.target.value) })} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button type="button" onClick={() => setShowModal(false)} className="bg-slate-700 px-4 py-2 rounded-lg text-slate-300">Cancel</button>
                <button type="submit" className="bg-indigo-600 px-4 py-2 rounded-lg text-white font-medium">Save Inbox</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
