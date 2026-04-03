import React, { useState } from 'react';

export function AIInsightsPanel({ insights, loading, onRefresh }) {
  // insights is expected to be the aiAnalysis state from App.jsx
  const [expanded, setExpanded] = useState(false);

  // Prefer structured analysis if available
  const structured = insights?.analysisStructured;
  const text = insights?.analysisText ?? insights?.analysis ?? "No analysis available";

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl shadow-sm border border-indigo-200 dark:border-indigo-800">
      <div className="p-4 border-b border-indigo-200 dark:border-indigo-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">AI Network Insights</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">Powered by AI analysis</p>
          </div>
        </div>
        <button 
          onClick={onRefresh}
          disabled={loading}
          className="p-2 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-lg transition-colors disabled:opacity-50"
        >
          <svg className={`w-5 h-5 text-indigo-600 dark:text-indigo-400 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
      <div className="p-4">
        {loading ? (
          <div className="flex items-center gap-3 py-6">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Analyzing network patterns...</span>
          </div>
        ) : structured ? (
          <div className="space-y-4">
            {/* Health Status */}
            {structured.health_status && (
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-2 h-2 rounded-full ${
                  structured.health_status === 'healthy'
                    ? 'bg-green-500'
                    : structured.health_status === 'warning'
                    ? 'bg-yellow-500'
                    : structured.health_status === 'degraded'
                    ? 'bg-red-500'
                    : 'bg-gray-400'
                }`}></span>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Health Status: <span className="capitalize">{structured.health_status}</span>
                </span>
              </div>
            )}
            {/* Summary */}
            {structured.summary && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Summary:</span>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{structured.summary}</p>
              </div>
            )}
            {/* Likely Causes */}
            {structured.likely_causes && Array.isArray(structured.likely_causes) && structured.likely_causes.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Likely Causes:</span>
                <ul className="list-disc pl-5 mt-1 text-sm text-gray-700 dark:text-gray-300">
                  {structured.likely_causes.map((cause, idx) => (
                    <li key={idx}>{cause}</li>
                  ))}
                </ul>
              </div>
            )}
            {/* Evidence */}
            {structured.evidence && Array.isArray(structured.evidence) && structured.evidence.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Evidence:</span>
                <ul className="list-disc pl-5 mt-1 text-sm text-gray-700 dark:text-gray-300">
                  {structured.evidence.map((ev, idx) => (
                    <li key={idx}>{ev}</li>
                  ))}
                </ul>
              </div>
            )}
            {/* Recommended Checks */}
            {structured.recommended_checks && Array.isArray(structured.recommended_checks) && structured.recommended_checks.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Recommended Checks:</span>
                <ul className="list-disc pl-5 mt-1 text-sm text-gray-700 dark:text-gray-300">
                  {structured.recommended_checks.map((chk, idx) => (
                    <li key={idx}>{chk}</li>
                  ))}
                </ul>
              </div>
            )}
            {/* Confidence */}
            {structured.confidence && (
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Confidence:</span>
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 font-semibold">{structured.confidence}</span>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">{text}</p>
          </div>
        )}
      </div>
    </div>
  );
}
