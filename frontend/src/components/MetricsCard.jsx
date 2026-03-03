import React from 'react';

const trendIcons = {
  up: (
    <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7H7" />
    </svg>
  ),
  down: (
    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10h10" />
    </svg>
  ),
  stable: (
    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  ),
};

const metricIcons = {
  latency: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  packetLoss: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
    </svg>
  ),
  bandwidth: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  jitter: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
};

const colorSchemes = {
  latency: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    icon: 'bg-blue-500',
    text: 'text-blue-700 dark:text-blue-300',
  },
  packetLoss: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    icon: 'bg-red-500',
    text: 'text-red-700 dark:text-red-300',
  },
  bandwidth: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    icon: 'bg-green-500',
    text: 'text-green-700 dark:text-green-300',
  },
  jitter: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    icon: 'bg-purple-500',
    text: 'text-purple-700 dark:text-purple-300',
  },
};

export function MetricsCard({ type, label, value, unit, trend, change, sparkline }) {
  const colors = colorSchemes[type] || colorSchemes.latency;
  const icon = metricIcons[type];
  const trendIcon = trendIcons[trend] || trendIcons.stable;

  return (
    <div className={`${colors.bg} rounded-lg p-2.5 border border-gray-200 dark:border-gray-700 transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-1">
        <div className={`${colors.icon} p-1 rounded text-white`}>
          {icon}
        </div>
        <div className="flex items-center gap-0.5">
          {trendIcon}
          <span className={`text-[10px] font-medium ${trend === 'up' ? 'text-red-500' : trend === 'down' ? 'text-green-500' : 'text-gray-500'}`}>
            {change}
          </span>
        </div>
      </div>
      <div>
        <p className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wide">{label}</p>
        <div className="flex items-baseline gap-0.5">
          <span className={`text-lg font-bold ${colors.text}`}>{value}</span>
          <span className="text-[10px] text-gray-500 dark:text-gray-400">{unit}</span>
        </div>
      </div>
      {sparkline && (
        <div className="mt-1 h-6">
          <MiniSparkline data={sparkline} color={colors.icon} />
        </div>
      )}
    </div>
  );
}

function MiniSparkline({ data, color }) {
  if (!data || data.length === 0) return null;
  
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 100;
  const height = 32;
  
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className={color.replace('bg-', 'text-')}
        points={points}
      />
    </svg>
  );
}

export function MetricsGrid({ metrics }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {metrics.map((metric, index) => (
        <MetricsCard key={index} {...metric} />
      ))}
    </div>
  );
}
