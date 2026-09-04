import React, { useState } from 'react';
import { X, CheckCircle2, Clock, ShieldCheck, Mail, ArrowRight, Copy, Check, ExternalLink, Code, Info } from 'lucide-react';

export default function LogDetailModal({ activity, onClose }) {
  const [copied, setCopied] = useState(false);
  const [showJson, setShowJson] = useState(false);

  if (!activity) return null;

  const handleCopyId = () => {
    if (activity.correlation_id) {
      navigator.clipboard.writeText(activity.correlation_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStepStatus = (stepName) => {
    const status = activity.status || '';
    if (status === 'ERROR' || status === 'FAILED') return 'error';
    
    if (stepName === 'DETECTED') return 'complete';
    if (stepName === 'CTA_VALIDATED') {
      if (['CTA_VALIDATED', 'CTA_CLICKED', 'REPLIED', 'COMPLETED'].includes(status)) return 'complete';
      if (['CTA_BLOCKED', 'CTA_NOT_FOUND'].includes(status)) return 'warning';
      return 'active';
    }
    if (stepName === 'CTA_CLICKED') {
      if (['CTA_CLICKED', 'REPLIED', 'COMPLETED'].includes(status)) return 'complete';
      if (status === 'CTA_VALIDATED') return 'active';
      return 'pending';
    }
    if (stepName === 'REPLIED') {
      if (['REPLIED', 'COMPLETED'].includes(status)) return 'complete';
      if (status === 'CTA_CLICKED') return 'active';
      return 'pending';
    }
    return 'pending';
  };

  const renderStepIcon = (state) => {
    if (state === 'complete') return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    if (state === 'warning') return <Clock className="w-5 h-5 text-amber-400" />;
    if (state === 'error') return <X className="w-5 h-5 text-rose-400" />;
    if (state === 'active') return <div className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />;
    return <div className="w-3 h-3 rounded-full bg-slate-700" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in" onClick={onClose}>
      <div 
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden animate-modal-slide"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Mail size={20} />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 truncate max-w-md">
                {activity.subject || 'Email Details'}
              </h2>
              <p className="text-xs text-slate-400 flex items-center gap-2">
                <span>Received: {activity.created_at || 'Just now'}</span>
                <span>•</span>
                <span className="font-mono text-indigo-300">ID #{activity.id}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">

          {/* Stepper Pipeline */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck size={14} className="text-indigo-400" />
              Workflow Execution Pipeline
            </div>
            <div className="grid grid-cols-4 gap-2 pt-2">
              {[
                { label: 'Detected', step: 'DETECTED' },
                { label: 'Extracted', step: 'CTA_VALIDATED' },
                { label: 'Clicked', step: 'CTA_CLICKED' },
                { label: 'Completed', step: 'REPLIED' },
              ].map(({ label, step }, i) => {
                const state = getStepStatus(step);
                return (
                  <div key={i} className="flex flex-col items-center text-center space-y-1.5">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-slate-900 border border-slate-700/60 shadow-inner">
                      {renderStepIcon(state)}
                    </div>
                    <span className={`text-xs font-medium ${state === 'complete' ? 'text-emerald-400' : state === 'warning' ? 'text-amber-400' : 'text-slate-400'}`}>
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 bg-slate-800/60 border border-slate-700/60 rounded-xl space-y-1">
              <span className="text-slate-400 font-medium">Inbox Account</span>
              <p className="text-slate-200 font-semibold truncate">{activity.inbox || 'N/A'}</p>
            </div>
            <div className="p-3.5 bg-slate-800/60 border border-slate-700/60 rounded-xl space-y-1">
              <span className="text-slate-400 font-medium">Sender Email</span>
              <p className="text-slate-200 font-semibold truncate">{activity.sender || 'N/A'}</p>
            </div>
            <div className="p-3.5 bg-slate-800/60 border border-slate-700/60 rounded-xl space-y-1 col-span-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-medium">Correlation Tracking ID</span>
                <button 
                  onClick={handleCopyId}
                  className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-sans"
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <p className="text-slate-300 font-mono text-xs truncate bg-slate-950/80 p-2 rounded border border-slate-800">
                {activity.correlation_id || 'N/A'}
              </p>
            </div>
          </div>

          {/* Detected Link Section */}
          <div className="p-4 bg-slate-800/40 border border-slate-700/60 rounded-xl space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <ExternalLink size={14} className="text-cyan-400" />
                Detected Call-to-Action Link
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                {activity.status || 'PROCESSED'}
              </span>
            </div>
            <p className="text-xs font-mono text-cyan-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800 break-all">
              {activity.cta_url || 'https://google.com (Extracted from body)'}
            </p>
          </div>

          {/* Raw JSON toggle */}
          <div className="space-y-2">
            <button
              onClick={() => setShowJson(!showJson)}
              className="text-xs font-medium text-slate-400 hover:text-indigo-400 flex items-center gap-1.5 transition"
            >
              <Code size={14} />
              <span>{showJson ? 'Hide Raw Activity Payload' : 'View Raw Activity Payload (JSON)'}</span>
            </button>
            {showJson && (
              <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                {JSON.stringify(activity, null, 2)}
              </pre>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-3.5 bg-slate-950/90 border-t border-slate-800 text-xs">
          <span className="text-slate-500 flex items-center gap-1">
            <Info size={13} /> Encrypted & Audited Transaction
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
