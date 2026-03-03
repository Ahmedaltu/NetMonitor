import React, { useMemo } from 'react';

export function NetworkChart({ data, title, yLabel, color = 'blue' }) {
  const chartConfig = useMemo(() => {
    if (!data || data.length === 0) return null;

    const values = data.map(d => d.value);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    const padding = range * 0.1;

    return {
      max: max + padding,
      min: Math.max(0, min - padding),
      range: range + padding * 2,
    };
  }, [data]);

  const colors = {
    blue: {
      line: '#3B82F6',
      fill: 'rgba(59, 130, 246, 0.1)',
      gradient: ['rgba(59, 130, 246, 0.3)', 'rgba(59, 130, 246, 0)'],
    },
    green: {
      line: '#10B981',
      fill: 'rgba(16, 185, 129, 0.1)',
      gradient: ['rgba(16, 185, 129, 0.3)', 'rgba(16, 185, 129, 0)'],
    },
    purple: {
      line: '#8B5CF6',
      fill: 'rgba(139, 92, 246, 0.1)',
      gradient: ['rgba(139, 92, 246, 0.3)', 'rgba(139, 92, 246, 0)'],
    },
    red: {
      line: '#EF4444',
      fill: 'rgba(239, 68, 68, 0.1)',
      gradient: ['rgba(239, 68, 68, 0.3)', 'rgba(239, 68, 68, 0)'],
    },
  };

  const colorSet = colors[color] || colors.blue;
  const width = 400;
  const height = 200;
  const paddingX = 50;
  const paddingY = 30;
  const chartWidth = width - paddingX * 2;
  const chartHeight = height - paddingY * 2;

  if (!chartConfig || !data || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">{title}</h3>
        <div className="h-36 flex items-center justify-center text-gray-400 text-sm">
          No data available
        </div>
      </div>
    );
  }

  const points = data.map((d, i) => {
    const x = paddingX + (i / (data.length - 1)) * chartWidth;
    const y = paddingY + chartHeight - ((d.value - chartConfig.min) / chartConfig.range) * chartHeight;
    return { x, y, ...d };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - paddingY} L ${paddingX} ${height - paddingY} Z`;

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(t => ({
    value: chartConfig.min + t * chartConfig.range,
    y: paddingY + chartHeight - t * chartHeight,
  }));

  const xTicks = data.filter((_, i) => i % Math.ceil(data.length / 5) === 0 || i === data.length - 1);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
        <span className="text-[10px] text-gray-500 dark:text-gray-400">{data.length} pts</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-36">
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={colorSet.gradient[0]} />
            <stop offset="100%" stopColor={colorSet.gradient[1]} />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={paddingX}
              y1={tick.y}
              x2={width - paddingX}
              y2={tick.y}
              stroke="currentColor"
              strokeOpacity={0.1}
              className="text-gray-400"
            />
            <text
              x={paddingX - 8}
              y={tick.y + 4}
              textAnchor="end"
              className="text-xs fill-gray-500 dark:fill-gray-400"
            >
              {tick.value.toFixed(1)}
            </text>
          </g>
        ))}

        {/* X-axis labels */}
        {xTicks.map((tick, i) => {
          const index = data.indexOf(tick);
          const x = paddingX + (index / (data.length - 1)) * chartWidth;
          return (
            <text
              key={i}
              x={x}
              y={height - 8}
              textAnchor="middle"
              className="text-xs fill-gray-500 dark:fill-gray-400"
            >
              {tick.label}
            </text>
          );
        })}

        {/* Area fill */}
        <path d={areaPath} fill={`url(#gradient-${color})`} />

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={colorSet.line}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="3"
            fill={colorSet.line}
            className="opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
          >
            <title>{`${p.label}: ${p.value.toFixed(2)} ${yLabel || ''}`}</title>
          </circle>
        ))}

        {/* Y-axis label */}
        <text
          x={15}
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90, 15, ${height / 2})`}
          className="text-xs fill-gray-500 dark:fill-gray-400"
        >
          {yLabel}
        </text>
      </svg>
    </div>
  );
}
