import React from 'react';

// Health state configuration
const healthConfig = {
  running: {
    color: 'bg-green-500',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    textColor: 'text-green-700 dark:text-green-300',
    borderColor: 'border-green-200 dark:border-green-800',
    label: 'Healthy',
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    ),
  },
  degraded: {
    color: 'bg-yellow-500',
    bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    textColor: 'text-yellow-700 dark:text-yellow-300',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    label: 'Degraded',
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
  },
  error: {
    color: 'bg-red-500',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    textColor: 'text-red-700 dark:text-red-300',
    borderColor: 'border-red-200 dark:border-red-800',
    label: 'Error',
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
  },
};

export function OperationalStatusPanel({ agentId, healthState, timeWindow, onTimeWindowChange, uptime, lastCheck }) {
  const state = healthState?.toLowerCase() || 'running';
  const config = healthConfig[state] || healthConfig.running;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-xl shadow-sm overflow-hidden`}>
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
          <div className={`${config.color} p-2 rounded-lg text-white`}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800 dark:text-gray-200">Agent Status</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">{agentId}</p>
            </div>
          </div>
          {onTimeWindowChange && (
            <select
              className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={timeWindow}
              onChange={e => onTimeWindowChange(e.target.value)}
            >
              <option value="5m">Last 5 min</option>
              <option value="15m">Last 15 min</option>
              <option value="1h">Last 1 hour</option>
              <option value="24h">Last 24 hours</option>
            </select>
          )}
        </div>

        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${config.color} animate-pulse`}></span>
              <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Status</span>
            </div>
            <div className={`mt-1 text-sm font-semibold ${config.textColor} flex items-center gap-1`}>
              {config.icon}
              {config.label}
            </div>
          </div>
          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Uptime</div>
            <div className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-200">
              {uptime || '99.9%'}
            </div>
          </div>
          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Last Check</div>
            <div className="mt-1 text-lg font-semibold text-gray-800 dark:text-gray-200">
              {lastCheck || 'Just now'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
