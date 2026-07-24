import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { MetricsGrid } from './components/MetricsCard';
import { NetworkChart } from './components/NetworkChart';
import { PacketLossEventsPanel } from './components/PacketLossEventsPanel';
import { LogStatusPanel } from './components/LogStatusPanel';
import { AlertsPanel } from './components/AlertsPanel';
import { TargetManager } from './components/TargetManager';
import { HttpProbesPanel, DnsProbesPanel } from './components/ProbesPanel';
import { TraceroutePanel } from './components/TraceroutePanel';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const api = (path, opts) =>
  fetch(`${API_BASE}${path}`, opts).then(res => res.ok ? res.json() : Promise.reject(`Request failed: ${path}`));

const timeFmt = ts => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

// KPI card definitions: key = history/sparkline field, src = /api/metrics field when it differs
const KPI_DEFS = [
  { key: 'latency', label: 'Avg Latency', unit: 'ms', type: 'latency', fmt: v => v.toFixed(1), trend: true, change: true },
  { key: 'rolling_mean', src: 'rolling_mean_latency', label: 'Rolling Mean', unit: 'ms', type: 'latency', fmt: v => v.toFixed(1), trend: true },
  { key: 'packet_loss', label: 'Packet Loss', unit: '%', type: 'packetLoss', fmt: v => (v * 100).toFixed(2) },
  { key: 'jitter', label: 'Jitter', unit: 'ms', type: 'jitter', fmt: v => v.toFixed(2), trend: true, change: true },
  { key: 'delay_spread', label: 'Delay Spread', unit: 'ms', type: 'latency', fmt: v => v.toFixed(1), trend: true },
  { key: 'rolling_std', src: 'rolling_std_latency', label: 'Std Dev', unit: 'ms', type: 'latency', fmt: v => v.toFixed(2), trend: true },
  { key: 'throughput', label: 'Throughput', unit: 'Mbps', type: 'bandwidth', fmt: v => v },
  { key: 'error_rate', label: 'Error Rate', unit: '%', type: 'packetLoss', fmt: v => (v * 100).toFixed(2) },
  { key: 'availability', label: 'Availability', unit: '%', type: 'latency', fmt: v => (v * 100).toFixed(2) },
  { key: 'uptime', label: 'Uptime', unit: '%', type: 'latency', fmt: v => v.toFixed(2) },
  { key: 'anomaly_score', label: 'Anomaly Score', unit: '', type: 'jitter', fmt: v => v.toFixed(2) },
  // invert: rising quality is good, so the trend arrows are flipped on purpose
  { key: 'quality_score', label: 'Quality Score', unit: '/100', type: 'quality', fmt: v => v.toFixed(1), trend: true, invert: true },
];

function generateSparklineFromHistory(history, key, count = 12) {
  if (!history || history.length === 0) return Array(count).fill(0);
  const values = history.slice(-count).map(h => h[key] ?? 0);
  return Array(count - values.length).fill(values[0] || 0).concat(values);
}

function generateChartDataFromHistory(history, key, count = 20) {
  if (!history || history.length === 0) return [];
  return history.slice(-count).map(h => ({ label: h.time, value: h[key] ?? 0 }));
}

const getTrend = (current, prev) => {
  if (prev === null || prev === undefined) return 'stable';
  if (current > prev * 1.05) return 'up';
  if (current < prev * 0.95) return 'down';
  return 'stable';
};

function buildMetrics(data, prevData, history) {
  return KPI_DEFS.map(def => {
    const v = data[def.src ?? def.key];
    const prevV = prevData?.[def.key];
    return {
      type: def.type === 'quality'
        ? (data.quality_score >= 80 ? 'latency' : data.quality_score >= 50 ? 'jitter' : 'packetLoss')
        : def.type,
      label: def.label,
      unit: def.unit,
      value: v == null ? '--' : def.fmt(v),
      trend: def.key === 'packet_loss' ? (v > 0 ? 'up' : 'stable')
        : !def.trend ? 'stable'
        : def.invert ? getTrend(prevV, v)
        : getTrend(v, prevV),
      change: def.change && prevV ? `${((v - prevV) / (prevV || 1) * 100).toFixed(1)}%` : '0%',
      sparkline: generateSparklineFromHistory(history, def.key),
    };
  });
}

const mapHistoryEntry = m => ({
  time: m.timestamp ? timeFmt(m.timestamp) : '',
  latency: m.latency,
  packet_loss: m.packet_loss,
  jitter: m.jitter,
  delay_spread: m.delay_spread,
  rolling_mean: m.rolling_mean_latency,
  rolling_std: m.rolling_std_latency,
});

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
  const [targets, setTargets] = useState([]);

  const [metrics, setMetrics] = useState(KPI_DEFS.map(d => ({
    type: d.type === 'quality' ? 'latency' : d.type,
    label: d.label,
    unit: d.unit,
    value: '--',
    trend: 'stable',
    change: '0%',
    sparkline: [],
  })));

  // Chart data
  const [latencyData, setLatencyData] = useState([]);
  const [jitterData, setJitterData] = useState([]);
  const [packetLossData, setPacketLossData] = useState([]);
  const [metricsHistory, setMetricsHistory] = useState([]);

  // Packet loss and events
  const [packetLoss, setPacketLoss] = useState(0);
  const [events, setEvents] = useState({
    timeouts: 0,
    packet_loss_count: 0,
    high_jitter_count: 0,
    recent: []
  });

  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);

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

  // Probe results
  const [httpProbes, setHttpProbes] = useState({});
  const [dnsProbes, setDnsProbes] = useState({});

  const setCharts = (hist) => {
    setLatencyData(generateChartDataFromHistory(hist, 'latency'));
    setJitterData(generateChartDataFromHistory(hist, 'jitter'));
    setPacketLossData(generateChartDataFromHistory(hist, 'packet_loss'));
  };

  const loadHistory = (target) => {
    const q = target ? `?target=${encodeURIComponent(target)}` : '';
    return api(`/api/metrics/history${q}`).then(data => {
      if (data.history && data.history.length > 0) {
        const hist = data.history.map(mapHistoryEntry);
        setMetricsHistory(hist);
        setCharts(hist);
      }
    });
  };

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    setLoading(true);
    api(`/api/agent/status?window=${timeWindow}`)
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
      api('/health')
        .then(data => {
          setAgentId(data.agent_id);
          setHealthState(data.state);
          setHealthDetails({
            lastError: data.last_error,
            lastCycle: data.last_cycle,
            consecutiveFailures: data.consecutive_failures
          });
          setMonitoringStatus(data.state === 'running' ? 'stable' : data.state === 'degraded' ? 'unstable' : 'disconnected');
        })
        .catch(() => setMonitoringStatus('disconnected'));
    };

    fetchHealthData();
    const interval = setInterval(fetchHealthData, 10000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  const handleFetchExplanation = () => {
    setAiAnalysis(prev => ({ ...prev, loading: true, error: null }));
    const windowMinutes = timeWindow === '5m' ? 5 : timeWindow === '15m' ? 15 : timeWindow === '1h' ? 60 : 1440;
    api(`/explain?window=${windowMinutes}`)
      .then(data => {
        setAiAnalysis(prev => ({
          ...prev,
          summary: data.summary,
          analysis: data.analysis, // backward compatibility
          analysisText: data.analysis_text ?? data.analysis ?? data.explanation ?? "",
          analysisStructured: data.analysis_structured ?? null,
          metricsSnapshot: data.metrics_snapshot ?? null,
          loading: false,
          error: null
        }));
      })
      .catch(() => {
        setAiAnalysis(prev => ({ ...prev, loading: false, error: 'Failed to fetch AI analysis' }));
      });
  };

  // Auto-refresh metrics every 10 seconds (only when monitoring)
  useEffect(() => {
    if (!isMonitoring) return;

    const fetchLatestMetrics = () => {
      api('/api/metrics')
        .then(data => {
          const timeLabel = timeFmt(Date.now());

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
              quality_score: data.quality_score,
            }].slice(-30);

            setCharts(newHistory);
            const prevData = prev.length > 1 ? prev[prev.length - 1] : null;
            setMetrics(buildMetrics(data, prevData, newHistory));
            setPacketLoss(data.packet_loss ?? 0);

            setLogs(prevLogs => [{
              time: timeLabel,
              level: data.packet_loss > 0 ? 'warn' : 'info',
              message: `Ping to target: ${data.latency?.toFixed(1) ?? 'N/A'}ms, Loss: ${((data.packet_loss ?? 0) * 100).toFixed(1)}%`
            }, ...prevLogs].slice(0, 50));

            return newHistory;
          });
        })
        .catch(err => console.error('Failed to fetch metrics:', err));
    };

    fetchLatestMetrics();
    const interval = setInterval(fetchLatestMetrics, 10000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Fetch events periodically
  useEffect(() => {
    if (!isMonitoring) return;
    const load = () => api('/api/events').then(setEvents).catch(err => console.error('Failed to fetch events:', err));
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Fetch probe results periodically
  useEffect(() => {
    if (!isMonitoring) return;
    const load = () => {
      api('/api/probes/http').then(d => setHttpProbes(d.probes || {})).catch(() => {});
      api('/api/probes/dns').then(d => setDnsProbes(d.probes || {})).catch(() => {});
    };
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Fetch initial target from backend
  useEffect(() => {
    api('/api/target').then(data => setMonitoredServer(data.target)).catch(() => {});
  }, []);

  // Fetch targets list periodically
  useEffect(() => {
    if (!isMonitoring) return;
    const load = () => api('/api/targets').then(data => setTargets(data.targets || [])).catch(() => {});
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Load server-side metrics history on mount
  useEffect(() => {
    loadHistory().catch(() => {});
  }, []);

  // Convert events to alerts for AlertsPanel
  useEffect(() => {
    if (events.recent && events.recent.length > 0) {
      setAlerts(events.recent.map((event, index) => ({
        id: `${event.type}-${event.time}-${index}`,
        severity: event.type === 'timeout' ? 'critical' : 'warning',
        time: event.time,
        title: event.type === 'timeout' ? 'Connection Timeout' :
               event.type === 'packet_loss' ? 'Packet Loss Detected' : 'High Jitter',
        message: event.message,
      })));
    } else {
      setAlerts([]);
    }
  }, [events]);

  const handleClearLogs = () => setLogs([]);
  const handleDismissAlert = (alertId) => setAlerts(prev => prev.filter(a => a.id !== alertId));
  const handleClearAlerts = () => setAlerts([]);

  const handleToggleMonitoring = () => {
    setMonitoringStatus(isMonitoring ? 'disconnected' : 'stable');
    setIsMonitoring(prev => !prev);
  };

  const handleServerChange = (newServer) => {
    setMonitoredServer(newServer);
    api(`/api/target?target=${encodeURIComponent(newServer)}`, { method: 'POST' })
      .then(data => console.log('Target updated to:', data.target))
      .catch(err => console.error('Failed to update target:', err));
  };

  const handleTargetSelect = (target) => {
    setMonitoredServer(target);
    api(`/api/target?target=${encodeURIComponent(target)}`, { method: 'POST' })
      .then(() => loadHistory(target))
      .catch(err => console.error('Failed to switch target:', err));
  };

  const reloadTargets = () => api('/api/targets').then(data => setTargets(data.targets || []));

  const handleAddTarget = (target) => {
    api(`/api/targets/add?target=${encodeURIComponent(target)}`, { method: 'POST' })
      .then(reloadTargets)
      .catch(err => console.error('Failed to add target:', err));
  };

  const handleRemoveTarget = (target) => {
    api(`/api/targets/remove?target=${encodeURIComponent(target)}`, { method: 'POST' })
      .then(reloadTargets)
      .catch(err => console.error('Failed to remove target:', err));
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
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
        onServerChange={handleServerChange}
        targets={targets}
        onTargetSelect={handleTargetSelect}
      />

      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">
        <TargetManager
          targets={targets}
          activeTarget={monitoredServer}
          onSelect={handleTargetSelect}
          onAdd={handleAddTarget}
          onRemove={handleRemoveTarget}
        />

        <MetricsGrid metrics={metrics} />

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

        <AlertsPanel
          alerts={alerts}
          onDismiss={handleDismissAlert}
          onClearAll={handleClearAlerts}
        />

        <TraceroutePanel target={monitoredServer} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <HttpProbesPanel probes={httpProbes} />
          <DnsProbesPanel probes={dnsProbes} />
        </div>

        {/* AI Analysis Panel */}
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
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Metrics snapshot:</span>
                  <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5">
                    {['latency','jitter','packet_loss','quality_score','availability','uptime'].map(k =>
                      aiAnalysis.summary[k] != null && (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500 dark:text-gray-400">{k.replace(/_/g, ' ')}</span>
                          <span className="text-gray-700 dark:text-gray-300 font-medium">
                            {typeof aiAnalysis.summary[k].mean === 'number'
                              ? aiAnalysis.summary[k].mean.toFixed(2)
                              : aiAnalysis.summary[k].mean ?? '—'}
                          </span>
                        </div>
                      )
                    )}
                  </div>
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

        {/* Health Details Panel */}
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

        <LogStatusPanel
          logs={logs}
          onClear={handleClearLogs}
        />
      </main>
    </div>
  );
}
