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

// Generate mock sparkline data
function generateSparkline(base, variance, count = 12) {
  return Array.from({ length: count }, () => base + (Math.random() - 0.5) * variance * 2);
}

// Generate mock chart data
function generateChartData(base, variance, count = 20) {
  const now = new Date();
  return Array.from({ length: count }, (_, i) => {
    const time = new Date(now - (count - 1 - i) * 60000);
    return {
      label: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      value: base + (Math.random() - 0.5) * variance * 2,
    };
  });
}

// Generate mock log entries
function generateLogs() {
  return [
    { time: '19:32:01', level: 'info', message: 'Ping test to 8.8.8.8 completed: 23ms' },
    { time: '19:31:45', level: 'info', message: 'Bandwidth test started' },
    { time: '19:31:30', level: 'warn', message: 'High latency spike detected: 156ms' },
    { time: '19:31:15', level: 'info', message: 'Agent collecting metrics...' },
    { time: '19:30:58', level: 'error', message: 'Connection timeout to 192.168.1.100' },
    { time: '19:30:45', level: 'info', message: 'Retransmission rate: 0.3%' },
  ];
}

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [agentId, setAgentId] = useState('agent-001');
  const [healthState, setHealthState] = useState('running');
  const [timeWindow, setTimeWindow] = useState('5m');
  const [loading, setLoading] = useState(false);
  
  // KPI Metrics (6 cards)
  const [metrics, setMetrics] = useState([
    { type: 'latency', label: 'Avg Latency', value: '23.5', unit: 'ms', trend: 'down', change: '-2.3%', sparkline: generateSparkline(23.5, 5) },
    { type: 'bandwidth', label: 'Throughput', value: '94.5', unit: 'Mbps', trend: 'up', change: '+5.2%', sparkline: generateSparkline(94.5, 10) },
    { type: 'packetLoss', label: 'Packet Loss', value: '0.02', unit: '%', trend: 'stable', change: '0%', sparkline: generateSparkline(0.02, 0.01) },
    { type: 'jitter', label: 'Jitter', value: '2.1', unit: 'ms', trend: 'down', change: '-0.5%', sparkline: generateSparkline(2.1, 0.8) },
    { type: 'latency', label: 'Retransmits', value: '0.3', unit: '%', trend: 'stable', change: '0%', sparkline: generateSparkline(0.3, 0.1) },
    { type: 'bandwidth', label: 'Uptime', value: '99.9', unit: '%', trend: 'stable', change: '0%', sparkline: generateSparkline(99.9, 0.1) },
  ]);

  // Chart data
  const [latencyData, setLatencyData] = useState(generateChartData(25, 8));
  const [throughputData, setThroughputData] = useState(generateChartData(90, 15));
  const [retransmitData, setRetransmitData] = useState(generateChartData(0.3, 0.2));

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
  const [logs, setLogs] = useState(generateLogs());

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

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => prev.map(m => ({
        ...m,
        sparkline: generateSparkline(parseFloat(m.value), parseFloat(m.value) * 0.2),
      })));
      setLatencyData(generateChartData(25, 8));
      setThroughputData(generateChartData(90, 15));
      setRetransmitData(generateChartData(0.3, 0.2));
      setPacketLoss(Math.random() * 0.1);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleClearLogs = useCallback(() => {
    setLogs([]);
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
      />
      
      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">
        {/* --------------------------------------------------------- */}
        {/* KPI CARDS (6 live indicators)                            */}
        {/* --------------------------------------------------------- */}
        <MetricsGrid metrics={metrics} />

        {/* --------------------------------------------------------- */}
        {/* LATENCY GRAPH  |  THROUGHPUT GRAPH                       */}
        {/* --------------------------------------------------------- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NetworkChart 
            data={latencyData} 
            title="Latency" 
            yLabel="ms"
            color="blue"
          />
          <NetworkChart 
            data={throughputData} 
            title="Throughput" 
            yLabel="Mbps"
            color="green"
          />
        </div>

        {/* --------------------------------------------------------- */}
        {/* RETRANSMISSIONS  |  PACKET LOSS + EVENTS                 */}
        {/* --------------------------------------------------------- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NetworkChart 
            data={retransmitData} 
            title="Retransmissions" 
            yLabel="%"
            color="purple"
          />
          <PacketLossEventsPanel 
            packetLoss={packetLoss} 
            events={events}
          />
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
