import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { MetricsGrid } from './components/MetricsCard';
import { NetworkChart } from './components/NetworkChart';
import { PacketLossEventsPanel } from './components/PacketLossEventsPanel';
import { LogStatusPanel } from './components/LogStatusPanel';

const API_BASE = 'http://localhost:8000';

function fetchAgentStatus(timeWindow) {
  return fetch(`${API_BASE}/api/agent/status?window=${timeWindow}`)
    .then(res => res.ok ? res.json() : Promise.reject('Failed to fetch'));
}

function fetchHealth() {
  return fetch(`${API_BASE}/health`)
    .then(res => res.ok ? res.json() : Promise.reject('Failed to fetch health'));
}

function fetchExplanation(windowMinutes = 30) {
  return fetch(`${API_BASE}/explain?window=${windowMinutes}`)
    .then(res => res.ok ? res.json() : Promise.reject('Failed to fetch explanation'));
}

function fetchMetrics() {
  return fetch(`${API_BASE}/api/metrics`)
    .then(res => res.ok ? res.json() : Promise.reject('Failed to fetch metrics'));
}

// Generate sparkline from history array
function generateSparklineFromHistory(history, key, count = 12) {
  if (!history || history.length === 0) {
    return Array(count).fill(0);
  }
  const values = history.slice(-count).map(h => h[key] ?? 0);
  while (values.length < count) {
    values.unshift(values[0] || 0);
  }
  return values;
}

// Generate chart data from history
function generateChartDataFromHistory(history, key, count = 20) {
  if (!history || history.length === 0) {
    return [];
  }
  return history.slice(-count).map(h => ({
    label: h.time,
    value: h[key] ?? 0,
  }));
}

// Initial log entries (empty - will be populated from real data)
function generateInitialLogs() {
  return [];
}

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [agentId, setAgentId] = useState('agent-001');
  const [healthState, setHealthState] = useState('running');
  const [timeWindow, setTimeWindow] = useState('5m');
  const [loading, setLoading] = useState(false);
  
  // Monitoring controls
  const [monitoredServer, setMonitoredServer] = useState('8.8.8.8');
  const [monitoringStatus, setMonitoringStatus] = useState('stable'); // stable, unstable, disconnected
  const [isMonitoring, setIsMonitoring] = useState(true);

  // KPI Metrics (6 cards)
  const [metrics, setMetrics] = useState([
    { type: 'latency', label: 'Avg Latency', value: '--', unit: 'ms', trend: 'stable', change: '0%', sparkline: [] },
    { type: 'latency', label: 'Rolling Mean', value: '--', unit: 'ms', trend: 'stable', change: '0%', sparkline: [] },
    { type: 'packetLoss', label: 'Packet Loss', value: '--', unit: '%', trend: 'stable', change: '0%', sparkline: [] },
    { type: 'jitter', label: 'Jitter', value: '--', unit: 'ms', trend: 'stable', change: '0%', sparkline: [] },
    { type: 'latency', label: 'Delay Spread', value: '--', unit: 'ms', trend: 'stable', change: '0%', sparkline: [] },
    { type: 'latency', label: 'Std Dev', value: '--', unit: 'ms', trend: 'stable', change: '0%', sparkline: [] },
  ]);

  // Chart data
  const [latencyData, setLatencyData] = useState([]);
  const [jitterData, setJitterData] = useState([]);
  const [packetLossData, setPacketLossData] = useState([]);

  // Metrics history for charts
  const [metricsHistory, setMetricsHistory] = useState([]);

  // Packet loss and events
  const [packetLoss, setPacketLoss] = useState(0.02);
  const [events, setEvents] = useState({
    timeouts: 3,
    duplicates: 12,
    outOfOrder: 5,
    recent: [
      { type: 'timeout', time: '19:30:58', message: 'Timeout to 192.168.1.100' },
      { type: 'duplicate', time: '19:28:12', message: 'Duplicate packet from 10.0.0.1' },
      { type: 'outOfOrder', time: '19:25:33', message: 'Out of order from gateway' },
    ]
  });

  // Logs
  const [logs, setLogs] = useState(generateInitialLogs());

  // Health details from /health endpoint
  const [healthDetails, setHealthDetails] = useState({
    lastError: null,
    lastCycle: null,
    consecutiveFailures: 0
  });

  // AI Analysis from /explain endpoint
  const [aiAnalysis, setAiAnalysis] = useState({
    summary: null,
    analysis: null,
    loading: false,
    error: null
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  useEffect(() => {
    setLoading(true);
    fetchAgentStatus(timeWindow)
      .then(data => {
        setAgentId(data.agentId);
        setHealthState(data.healthState);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [timeWindow]);

  // Fetch health details periodically
  useEffect(() => {
    if (!isMonitoring) return;

    const fetchHealthData = () => {
      fetchHealth()
        .then(data => {
          setAgentId(data.agent_id);
          setHealthState(data.state);
          setHealthDetails({
            lastError: data.last_error,
            lastCycle: data.last_cycle,
            consecutiveFailures: data.consecutive_failures
          });
          // Update monitoring status based on health
          if (data.state === 'running') {
            setMonitoringStatus('stable');
          } else if (data.state === 'degraded') {
            setMonitoringStatus('unstable');
          } else {
            setMonitoringStatus('disconnected');
          }
        })
        .catch(() => {
          setMonitoringStatus('disconnected');
        });
    };

    fetchHealthData();
    const interval = setInterval(fetchHealthData, 10000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Fetch AI explanation
  const handleFetchExplanation = useCallback(() => {
    setAiAnalysis(prev => ({ ...prev, loading: true, error: null }));
    const windowMinutes = timeWindow === '5m' ? 5 : timeWindow === '15m' ? 15 : timeWindow === '1h' ? 60 : 1440;
    fetchExplanation(windowMinutes)
      .then(data => {
        setAiAnalysis({
          summary: data.summary,
          analysis: data.analysis,
          loading: false,
          error: null
        });
      })
      .catch(err => {
        setAiAnalysis(prev => ({
          ...prev,
          loading: false,
          error: 'Failed to fetch AI analysis'
        }));
      });
  }, [timeWindow]);

  // Auto-refresh data every 10 seconds (only when monitoring)
  useEffect(() => {
    if (!isMonitoring) return;

    const fetchLatestMetrics = () => {
      fetchMetrics()
        .then(data => {
          // Get current time for chart labels
          const now = new Date();
          const timeLabel = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          
          // Add to history (keep last 30 points)
          setMetricsHistory(prev => {
            const newHistory = [...prev, {
              time: timeLabel,
              latency: data.latency,
              packet_loss: data.packet_loss,
              jitter: data.jitter,
              delay_spread: data.delay_spread,
              rolling_mean: data.rolling_mean_latency,
              rolling_std: data.rolling_std_latency,
            }].slice(-30);
            
            // Update chart data from history
            setLatencyData(generateChartDataFromHistory(newHistory, 'latency'));
            setJitterData(generateChartDataFromHistory(newHistory, 'jitter'));
            setPacketLossData(generateChartDataFromHistory(newHistory, 'packet_loss'));
            
            // Calculate trends
            const getTrend = (current, prev) => {
              if (prev === null || prev === undefined) return 'stable';
              if (current > prev * 1.05) return 'up';
              if (current < prev * 0.95) return 'down';
              return 'stable';
            };
            
            const prevData = prev.length > 1 ? prev[prev.length - 1] : null;
            
            // Update KPI metrics with real data
            setMetrics([
              { 
                type: 'latency', 
                label: 'Avg Latency', 
                value: data.latency?.toFixed(1) ?? '--', 
                unit: 'ms', 
                trend: getTrend(data.latency, prevData?.latency),
                change: prevData?.latency ? `${((data.latency - prevData.latency) / prevData.latency * 100).toFixed(1)}%` : '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'latency')
              },
              { 
                type: 'latency', 
                label: 'Rolling Mean', 
                value: data.rolling_mean_latency?.toFixed(1) ?? '--', 
                unit: 'ms', 
                trend: getTrend(data.rolling_mean_latency, prevData?.rolling_mean),
                change: '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'rolling_mean')
              },
              { 
                type: 'packetLoss', 
                label: 'Packet Loss', 
                value: data.packet_loss !== null ? (data.packet_loss * 100).toFixed(2) : '--', 
                unit: '%', 
                trend: data.packet_loss > 0 ? 'up' : 'stable',
                change: '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'packet_loss')
              },
              { 
                type: 'jitter', 
                label: 'Jitter', 
                value: data.jitter?.toFixed(2) ?? '--', 
                unit: 'ms', 
                trend: getTrend(data.jitter, prevData?.jitter),
                change: prevData?.jitter ? `${((data.jitter - prevData.jitter) / (prevData.jitter || 1) * 100).toFixed(1)}%` : '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'jitter')
              },
              { 
                type: 'latency', 
                label: 'Delay Spread', 
                value: data.delay_spread?.toFixed(1) ?? '--', 
                unit: 'ms', 
                trend: getTrend(data.delay_spread, prevData?.delay_spread),
                change: '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'delay_spread')
              },
              { 
                type: 'latency', 
                label: 'Std Dev', 
                value: data.rolling_std_latency?.toFixed(2) ?? '--', 
                unit: 'ms', 
                trend: getTrend(data.rolling_std_latency, prevData?.rolling_std),
                change: '0%',
                sparkline: generateSparklineFromHistory(newHistory, 'rolling_std')
              },
            ]);
            
            // Update packet loss for the gauge panel
            setPacketLoss(data.packet_loss ?? 0);
            
            // Add log entry for the metrics fetch
            setLogs(prevLogs => {
              const newLog = {
                time: timeLabel,
                level: data.packet_loss > 0 ? 'warn' : 'info',
                message: `Ping to target: ${data.latency?.toFixed(1) ?? 'N/A'}ms, Loss: ${((data.packet_loss ?? 0) * 100).toFixed(1)}%`
              };
              return [newLog, ...prevLogs].slice(0, 50);
            });
            
            return newHistory;
          });
        })
        .catch(err => {
          console.error('Failed to fetch metrics:', err);
        });
    };

    // Fetch immediately and then every 10 seconds
    fetchLatestMetrics();
    const interval = setInterval(fetchLatestMetrics, 10000);

    return () => clearInterval(interval);
  }, [isMonitoring]);

  const handleClearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const handleToggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => {
      if (prev) {
        // Stopping monitoring
        setMonitoringStatus('disconnected');
      } else {
        // Starting monitoring
        setMonitoringStatus('stable');
      }
      return !prev;
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      {/* --------------------------------------------------------- */}
      {/* HEADER BAR                                                */}
      {/* --------------------------------------------------------- */}
      <Header 
        darkMode={darkMode} 
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        agentId={agentId}
        healthState={healthState}
        timeWindow={timeWindow}
        onTimeWindowChange={setTimeWindow}
        monitoredServer={monitoredServer}
        monitoringStatus={monitoringStatus}
        isMonitoring={isMonitoring}
        onToggleMonitoring={handleToggleMonitoring}
        onServerChange={setMonitoredServer}
      />
      
      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">
        {/* --------------------------------------------------------- */}
        {/* KPI CARDS (6 live indicators)                            */}
        {/* --------------------------------------------------------- */}
        <MetricsGrid metrics={metrics} />

        {/* --------------------------------------------------------- */}
        {/* LATENCY GRAPH  |  JITTER GRAPH                           */}
        {/* --------------------------------------------------------- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NetworkChart 
            data={latencyData} 
            title="Latency (Live)" 
            yLabel="ms"
            color="blue"
          />
          <NetworkChart 
            data={jitterData} 
            title="Jitter (Live)" 
            yLabel="ms"
            color="green"
          />
        </div>

        {/* --------------------------------------------------------- */}
        {/* PACKET LOSS CHART  |  PACKET LOSS + EVENTS               */}
        {/* --------------------------------------------------------- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NetworkChart 
            data={packetLossData} 
            title="Packet Loss (Live)" 
            yLabel="%"
            color="purple"
          />
          <PacketLossEventsPanel 
            packetLoss={packetLoss} 
            events={events}
          />
        </div>

        {/* --------------------------------------------------------- */}
        {/* AI ANALYSIS PANEL                                        */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              AI Network Analysis
            </h3>
            <button
              onClick={handleFetchExplanation}
              disabled={aiAnalysis.loading}
              className="px-3 py-1 bg-purple-500 hover:bg-purple-600 disabled:bg-purple-300 text-white text-xs rounded-lg transition-colors flex items-center gap-1"
            >
              {aiAnalysis.loading ? (
                <>
                  <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Analyze
                </>
              )}
            </button>
          </div>
          
          {aiAnalysis.error && (
            <div className="text-red-500 text-xs mb-2">{aiAnalysis.error}</div>
          )}
          
          {aiAnalysis.analysis ? (
            <div className="space-y-2">
              {aiAnalysis.summary && (
                <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Summary:</span>
                  <p className="text-xs text-gray-700 dark:text-gray-300 mt-1">{JSON.stringify(aiAnalysis.summary)}</p>
                </div>
              )}
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded p-2">
                <span className="text-xs font-medium text-purple-600 dark:text-purple-400">Analysis:</span>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1 whitespace-pre-wrap">{aiAnalysis.analysis}</p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500 dark:text-gray-400">Click "Analyze" to get AI-powered insights about your network performance.</p>
          )}
        </div>

        {/* --------------------------------------------------------- */}
        {/* HEALTH DETAILS PANEL                                     */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Agent Health Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">Agent ID</span>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{agentId}</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">State</span>
              <p className={`text-sm font-medium ${healthState === 'running' ? 'text-green-600' : healthState === 'degraded' ? 'text-yellow-600' : 'text-red-600'}`}>
                {healthState}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">Last Cycle</span>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                {healthDetails.lastCycle ? new Date(healthDetails.lastCycle).toLocaleTimeString() : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">Failures</span>
              <p className={`text-sm font-medium ${healthDetails.consecutiveFailures > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {healthDetails.consecutiveFailures}
              </p>
            </div>
          </div>
          {healthDetails.lastError && (
            <div className="mt-2 bg-red-50 dark:bg-red-900/20 rounded p-2">
              <span className="text-xs text-red-600 dark:text-red-400">Last Error:</span>
              <p className="text-xs text-red-700 dark:text-red-300">{healthDetails.lastError}</p>
            </div>
          )}
        </div>

        {/* --------------------------------------------------------- */}
        {/* LOG / STATUS PANEL                                       */}
        {/* --------------------------------------------------------- */}
        <LogStatusPanel 
          logs={logs}
          onClear={handleClearLogs}
        />
      </main>
    </div>
  );
}
