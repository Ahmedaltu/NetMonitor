import React from 'react';

export function PacketLossEventsPanel({ packetLoss, events }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 h-full">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Packet Loss & Events</h3>
      </div>
      <div className="p-3 grid grid-cols-2 gap-3">
        {/* Packet Loss Gauge */}
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Packet Loss</div>
          <div className="flex items-end gap-1">
            <span className={`text-2xl font-bold ${
              packetLoss < 1 ? 'text-green-600 dark:text-green-400' :
              packetLoss < 5 ? 'text-yellow-600 dark:text-yellow-400' :
              'text-red-600 dark:text-red-400'
            }`}>{packetLoss.toFixed(2)}</span>
            <span className="text-sm text-gray-500 dark:text-gray-400 mb-0.5">%</span>
          </div>
          <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all ${
                packetLoss < 1 ? 'bg-green-500' :
                packetLoss < 5 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{ width: `${Math.min(packetLoss * 10, 100)}%` }}
            />
          </div>
        </div>

        {/* Events Summary */}
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Network Events</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-300">Timeouts</span>
              <span className="font-medium text-red-600 dark:text-red-400">{events.timeouts || 0}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-300">Packet Loss</span>
              <span className="font-medium text-yellow-600 dark:text-yellow-400">{events.packet_loss_count || 0}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-300">High Jitter</span>
              <span className="font-medium text-orange-600 dark:text-orange-400">{events.high_jitter_count || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Events List */}
      <div className="px-3 pb-3">
        <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Recent Events</div>
        <div className="space-y-1 max-h-24 overflow-y-auto">
          {events.recent && events.recent.length > 0 ? (
            events.recent.map((event, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  event.type === 'timeout' ? 'bg-red-500' :
                  event.type === 'packet_loss' ? 'bg-yellow-500' :
                  event.type === 'high_jitter' ? 'bg-orange-500' :
                  'bg-gray-500'
                }`}></span>
                <span className="text-gray-400 dark:text-gray-500">{event.time}</span>
                <span className="text-gray-600 dark:text-gray-300 truncate">{event.message}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-400 dark:text-gray-500">No recent events</div>
          )}
        </div>
      </div>
    </div>
  );
}
