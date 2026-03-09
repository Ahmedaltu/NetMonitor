import React from 'react';

export function HttpProbesPanel({ probes }) {
  const items = Array.isArray(probes) ? probes : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
        </svg>
        HTTP Probes
      </h3>
      {items.length === 0 ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">No HTTP probes configured.</p>
      ) : (
        <div className="space-y-2">
          {items.map((probe) => {
            const ok = probe.success;
            return (
              <div key={probe.url} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded p-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-gray-700 dark:text-gray-300 truncate">{probe.url}</span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`text-xs font-medium ${ok ? 'text-green-600' : 'text-red-600'}`}>
                    {probe.status_code ?? 'ERR'}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {probe.response_time_ms != null ? `${probe.response_time_ms.toFixed(0)}ms` : '--'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function DnsProbesPanel({ probes }) {
  const items = Array.isArray(probes) ? probes : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
        </svg>
        DNS Probes
      </h3>
      {items.length === 0 ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">No DNS probes configured.</p>
      ) : (
        <div className="space-y-2">
          {items.map((probe) => {
            const ok = probe.success;
            return (
              <div key={probe.hostname} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded p-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-gray-700 dark:text-gray-300 truncate">{probe.hostname}</span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {probe.resolution_time_ms != null ? `${probe.resolution_time_ms.toFixed(1)}ms` : '--'}
                  </span>
                  {probe.resolved_ips && probe.resolved_ips.length > 0 && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">{probe.resolved_ips[0]}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
