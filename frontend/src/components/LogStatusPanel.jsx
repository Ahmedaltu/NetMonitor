import React from 'react';

export function LogStatusPanel({ logs, onClear }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">System Logs</h3>
          <span className="text-xs text-gray-500 dark:text-gray-400">({logs.length} entries)</span>
        </div>
        {logs.length > 0 && onClear && (
          <button 
            onClick={onClear}
            className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            Clear
          </button>
        )}
      </div>
      <div className="p-2 h-40 overflow-y-auto font-mono text-xs">
        {logs.length === 0 ? (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            No log entries
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div 
                key={index} 
                className={`flex gap-2 px-2 py-1 rounded ${
                  log.level === 'error' ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300' :
                  log.level === 'warn' ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300' :
                  log.level === 'info' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' :
                  'bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <span className="text-gray-400 dark:text-gray-500 flex-shrink-0">{log.time}</span>
                <span className={`uppercase w-10 flex-shrink-0 font-medium ${
                  log.level === 'error' ? 'text-red-600 dark:text-red-400' :
                  log.level === 'warn' ? 'text-yellow-600 dark:text-yellow-400' :
                  log.level === 'info' ? 'text-blue-600 dark:text-blue-400' :
                  'text-gray-500'
                }`}>[{log.level}]</span>
                <span className="flex-1 truncate">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
