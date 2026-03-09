import React, { useState } from 'react';

export function TargetManager({ targets, activeTarget, onSelect, onAdd, onRemove }) {
  const [newTarget, setNewTarget] = useState('');
  const [error, setError] = useState(null);

  const handleAdd = () => {
    const trimmed = newTarget.trim();
    if (!trimmed) return;
    if (targets.some(t => t.target === trimmed)) {
      setError('Target already exists');
      return;
    }
    setError(null);
    onAdd(trimmed);
    setNewTarget('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAdd();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
        </svg>
        Monitoring Targets
      </h3>

      {/* Add target */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newTarget}
          onChange={e => { setNewTarget(e.target.value); setError(null); }}
          onKeyDown={handleKeyDown}
          placeholder="Add hostname or IP (e.g. 1.1.1.1)"
          className="flex-1 px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <button
          onClick={handleAdd}
          className="px-3 py-1.5 bg-indigo-500 hover:bg-indigo-600 text-white text-sm rounded-lg transition-colors flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add
        </button>
      </div>
      {error && <p className="text-xs text-red-500 mb-2">{error}</p>}

      {/* Targets list */}
      <div className="space-y-1.5">
        {targets.length === 0 && (
          <p className="text-xs text-gray-400 dark:text-gray-500">No targets configured.</p>
        )}
        {targets.map(t => {
          const isActive = t.target === activeTarget;
          return (
            <div
              key={t.target}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700'
                  : 'bg-gray-50 dark:bg-gray-700 border border-transparent hover:border-gray-200 dark:hover:border-gray-600'
              }`}
            >
              <button
                onClick={() => onSelect(t.target)}
                className="flex items-center gap-2 flex-1 text-left"
              >
                <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-indigo-500 animate-pulse' : 'bg-gray-300 dark:bg-gray-500'}`} />
                <span className="font-medium text-gray-800 dark:text-gray-200">{t.target}</span>
                {t.quality_score != null && (
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    t.quality_score >= 80 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    t.quality_score >= 50 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {t.quality_score.toFixed(0)}/100
                  </span>
                )}
                {t.latency != null && (
                  <span className="text-xs text-gray-400 dark:text-gray-500">{t.latency.toFixed(1)}ms</span>
                )}
                {isActive && (
                  <span className="text-xs text-indigo-500 dark:text-indigo-400 font-medium">active</span>
                )}
              </button>
              <button
                onClick={() => onRemove(t.target)}
                className="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors rounded"
                title="Remove target"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
