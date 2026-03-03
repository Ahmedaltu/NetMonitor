import React from 'react';

const healthColors = {
  running: 'bg-green-500',
  degraded: 'bg-yellow-500',
  error: 'bg-red-500',
};

export function Header({ darkMode, onToggleDarkMode, agentId, healthState, timeWindow, onTimeWindowChange }) {
  const healthColor = healthColors[healthState?.toLowerCase()] || 'bg-gray-400';

  return (
    <header className="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-gray-800 dark:to-gray-900 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">NetMonitor</h1>
          </div>
        </div>

        {/* Center: Agent Status */}
        <div className="hidden md:flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
            <span className={`w-2 h-2 rounded-full ${healthColor} animate-pulse`}></span>
            <span className="text-sm text-white/90">{agentId || 'agent-001'}</span>
            <span className="text-xs text-white/60 capitalize">({healthState || 'running'})</span>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-3">
          {/* Time Window Selector */}
          {onTimeWindowChange && (
            <select
              className="bg-white/10 border border-white/20 rounded-lg px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-white/30"
              value={timeWindow}
              onChange={e => onTimeWindowChange(e.target.value)}
            >
              <option value="5m" className="text-gray-800">5 min</option>
              <option value="15m" className="text-gray-800">15 min</option>
              <option value="1h" className="text-gray-800">1 hour</option>
              <option value="24h" className="text-gray-800">24 hours</option>
            </select>
          )}

          {/* Dark Mode Toggle */}
          <button
            onClick={onToggleDarkMode}
            className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            {darkMode ? (
              <svg className="w-4 h-4 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>

          {/* Live Indicator */}
          <div className="flex items-center gap-1.5 text-white">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span className="text-xs">Live</span>
          </div>
        </div>
      </div>
    </header>
  );
}
