import React from 'react';

const healthColors = {
  running: 'bg-green-500',
  degraded: 'bg-yellow-500',
  error: 'bg-red-500',
};

const monitoringStatusConfig = {
  stable: { color: 'bg-green-500', label: 'Stable', emoji: '🟢' },
  unstable: { color: 'bg-yellow-500', label: 'Unstable', emoji: '🟡' },
  disconnected: { color: 'bg-red-500', label: 'Disconnected', emoji: '🔴' },
};

export function Header({ 
  darkMode, 
  onToggleDarkMode, 
  agentId, 
  healthState, 
  timeWindow, 
  onTimeWindowChange,
  monitoredServer,
  monitoringStatus,
  isMonitoring,
  onToggleMonitoring,
  onServerChange
}) {
  const healthColor = healthColors[healthState?.toLowerCase()] || 'bg-gray-400';
  const statusConfig = monitoringStatusConfig[monitoringStatus] || monitoringStatusConfig.disconnected;

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

        {/* Center: Monitored Server & Status */}
        <div className="hidden md:flex items-center gap-3">
          {/* Server Input */}
          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-2 py-1">
            <svg className="w-3.5 h-3.5 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
            </svg>
            <input
              type="text"
              value={monitoredServer || '8.8.8.8'}
              onChange={e => onServerChange?.(e.target.value)}
              placeholder="8.8.8.8"
              className="bg-transparent text-white text-sm w-24 placeholder-white/50 focus:outline-none"
            />
          </div>

          {/* Monitoring Status */}
          <div className="flex items-center gap-1.5 bg-white/10 rounded-lg px-2 py-1">
            <span className="text-sm">{statusConfig.emoji}</span>
            <span className="text-xs text-white/90">{statusConfig.label}</span>
          </div>

          {/* Start/Stop Button */}
          <button
            onClick={onToggleMonitoring}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              isMonitoring 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {isMonitoring ? (
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                </svg>
                Stop
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                Start
              </span>
            )}
          </button>

          {/* Agent Status */}
          <div className="flex items-center gap-1.5 bg-white/10 rounded-lg px-2 py-1">
            <span className={`w-1.5 h-1.5 rounded-full ${healthColor} animate-pulse`}></span>
            <span className="text-xs text-white/80">{agentId || 'agent-001'}</span>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-2">
          {/* Time Window Selector */}
          {onTimeWindowChange && (
            <select
              className="bg-white/10 border border-white/20 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-white/30"
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
          <div className="flex items-center gap-1 text-white">
            <span className={`w-2 h-2 rounded-full ${isMonitoring ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></span>
            <span className="text-xs">{isMonitoring ? 'Live' : 'Paused'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
