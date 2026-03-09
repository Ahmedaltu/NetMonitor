import React, { useState, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function TraceroutePanel({ target }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runTraceroute = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = target ? `?target=${encodeURIComponent(target)}` : '';
    fetch(`${API_BASE}/api/traceroute${params}`, { method: 'POST' })
      .then(res => res.ok ? res.json() : Promise.reject('Traceroute failed'))
      .then(data => {
        setResult(data.traceroute);
        setLoading(false);
      })
      .catch(err => {
        setError(String(err));
        setLoading(false);
      });
  }, [target]);

  const hops = result?.hops || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          Traceroute
          {result?.target && (
            <span className="text-xs text-gray-400 font-normal">to {result.target}</span>
          )}
        </h3>
        <button
          onClick={runTraceroute}
          disabled={loading}
          className="px-3 py-1 bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 text-white text-xs rounded-lg transition-colors"
        >
          {loading ? 'Running...' : 'Run Traceroute'}
        </button>
      </div>

      {error && <p className="text-xs text-red-500 mb-2">{error}</p>}

      {hops.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 dark:text-gray-400 border-b dark:border-gray-700">
                <th className="py-1 px-2 text-left">Hop</th>
                <th className="py-1 px-2 text-left">IP</th>
                <th className="py-1 px-2 text-right">Avg RTT</th>
                <th className="py-1 px-2 text-left">Bar</th>
              </tr>
            </thead>
            <tbody>
              {(() => {
                const maxRtt = Math.max(...hops.filter(h => h.avg_rtt).map(h => h.avg_rtt), 1);
                return hops.map((hop) => {
                const pct = hop.avg_rtt ? Math.min((hop.avg_rtt / maxRtt) * 100, 100) : 0;
                const color = hop.avg_rtt == null ? 'bg-gray-300' :
                  hop.avg_rtt < 20 ? 'bg-green-500' :
                  hop.avg_rtt < 50 ? 'bg-yellow-500' :
                  hop.avg_rtt < 100 ? 'bg-orange-500' : 'bg-red-500';
                return (
                  <tr key={hop.hop} className="border-b dark:border-gray-700/50">
                    <td className="py-1 px-2 text-gray-600 dark:text-gray-400">{hop.hop}</td>
                    <td className="py-1 px-2 text-gray-700 dark:text-gray-300 font-mono">{hop.ip || '*'}</td>
                    <td className="py-1 px-2 text-right text-gray-700 dark:text-gray-300">
                      {hop.avg_rtt != null ? `${hop.avg_rtt.toFixed(1)}ms` : '*'}
                    </td>
                    <td className="py-1 px-2 w-1/3">
                      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                    </td>
                  </tr>
                );
              });
              })()}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-xs text-gray-500 dark:text-gray-400">Click "Run Traceroute" to trace the route to the target.</p>
      )}
    </div>
  );
}
