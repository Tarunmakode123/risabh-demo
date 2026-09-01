import React, { useEffect, useState } from 'react';
import API from '../services/api';
import { Save, Plus, Trash2 } from 'lucide-react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    allowed_cta_domains: '',
    allowed_sender_domains: '',
    cta_selector: '',
    min_reply_delay: 30,
    max_reply_delay: 180
  });

  const [templates, setTemplates] = useState([]);
  const [newTmpl, setNewTmpl] = useState({ name: '', body: '' });
  const [savedMsg, setSavedMsg] = useState('');

  const fetchSettings = async () => {
    try {
      const [setRes, tmplRes] = await Promise.all([
        API.get('/api/settings'),
        API.get('/api/settings/templates')
      ]);
      setSettings(setRes.data);
      setTemplates(tmplRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      await API.put('/api/settings', settings);
      setSavedMsg('Settings updated successfully!');
      setTimeout(() => setSavedMsg(''), 3000);
    } catch (err) {
      alert('Error updating settings: ' + err.message);
    }
  };

  const handleAddTemplate = async (e) => {
    e.preventDefault();
    if (!newTmpl.name || !newTmpl.body) return;
    try {
      await API.post('/api/settings/templates', newTmpl);
      setNewTmpl({ name: '', body: '' });
      fetchSettings();
    } catch (err) {
      alert('Error creating template: ' + err.message);
    }
  };

  const handleDeleteTemplate = async (id) => {
    await API.delete(`/api/settings/templates/${id}`);
    fetchSettings();
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">System Configuration</h1>
        <p className="text-slate-400 text-xs">Configure security allowlists, CTA selectors, reply delays, and response templates.</p>
      </div>

      {savedMsg && (
        <div className="bg-emerald-950 border border-emerald-800 text-emerald-300 p-3 rounded-lg text-xs">
          {savedMsg}
        </div>
      )}

      {/* Security & Allowlists Form */}
      <form onSubmit={handleSaveSettings} className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4 shadow-lg text-xs">
        <h3 className="text-sm font-semibold text-indigo-400 border-b border-slate-700 pb-2">Security Allowlists</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-slate-300 font-medium mb-1">ALLOWED_CTA_DOMAINS (Comma-separated)</label>
            <input
              type="text"
              value={settings.allowed_cta_domains || ''}
              onChange={(e) => setSettings({ ...settings, allowed_cta_domains: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
              placeholder="test.example.com, landing.arrowmail.internal"
            />
          </div>
          <div>
            <label className="block text-slate-300 font-medium mb-1">ALLOWED_SENDER_DOMAINS (Comma-separated)</label>
            <input
              type="text"
              value={settings.allowed_sender_domains || ''}
              onChange={(e) => setSettings({ ...settings, allowed_sender_domains: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
              placeholder="example.com, greenarrow.internal"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-2">
          <div>
            <label className="block text-slate-300 font-medium mb-1">CTA Selector (CSS/HTML)</label>
            <input
              type="text"
              value={settings.cta_selector || ''}
              onChange={(e) => setSettings({ ...settings, cta_selector: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
              placeholder="a.cta-button"
            />
          </div>
          <div>
            <label className="block text-slate-300 font-medium mb-1">Min Reply Delay (Seconds)</label>
            <input
              type="number"
              value={settings.min_reply_delay || 30}
              onChange={(e) => setSettings({ ...settings, min_reply_delay: parseInt(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
            />
          </div>
          <div>
            <label className="block text-slate-300 font-medium mb-1">Max Reply Delay (Seconds)</label>
            <input
              type="number"
              value={settings.max_reply_delay || 180}
              onChange={(e) => setSettings({ ...settings, max_reply_delay: parseInt(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
            />
          </div>
        </div>

        <div className="flex justify-end pt-3">
          <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg flex items-center gap-2">
            <Save size={14} /> Save Configuration
          </button>
        </div>
      </form>

      {/* Reply Templates */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4 shadow-lg text-xs">
        <h3 className="text-sm font-semibold text-purple-400 border-b border-slate-700 pb-2">Configured Reply Templates</h3>

        <div className="space-y-3">
          {templates.map((t) => (
            <div key={t.id} className="bg-slate-900/60 border border-slate-700/60 p-3 rounded-lg flex justify-between items-center">
              <div>
                <strong className="text-slate-200 block text-xs mb-0.5">{t.name}</strong>
                <p className="text-slate-400 font-mono text-xs">{t.body}</p>
              </div>
              <button onClick={() => handleDeleteTemplate(t.id)} className="text-rose-400 hover:text-rose-300 p-1">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        {/* Add Template */}
        <form onSubmit={handleAddTemplate} className="space-y-3 pt-3 border-t border-slate-700/60">
          <h4 className="font-semibold text-slate-300">Add New Reply Template</h4>
          <div className="grid grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Template Name (e.g. Friendly Ack)"
              value={newTmpl.name}
              onChange={(e) => setNewTmpl({ ...newTmpl, name: e.target.value })}
              className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
            />
            <input
              type="text"
              placeholder="Reply Text (e.g. Thanks for sharing this.)"
              value={newTmpl.body}
              onChange={(e) => setNewTmpl({ ...newTmpl, body: e.target.value })}
              className="col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200"
            />
          </div>
          <button type="submit" className="bg-purple-600 hover:bg-purple-500 text-white font-medium px-4 py-2 rounded-lg flex items-center gap-2">
            <Plus size={14} /> Add Template
          </button>
        </form>
      </div>
    </div>
  );
}
