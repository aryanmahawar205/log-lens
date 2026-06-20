import { useState, useEffect } from 'react';

// Basic type definitions
interface TrafficSummary {
  total_requests: number;
  total_bytes: number;
  unique_visitors: number;
}

export function Dashboard() {
  const [summary, setSummary] = useState<TrafficSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, this would fetch from the FastAPI backend
    // fetch('http://localhost:8000/api/v1/analytics/summary')
    //   .then(res => res.json())
    //   .then(data => { setSummary(data); setLoading(false); })
    //   .catch(err => console.error(err));

    // Mock data for initial scaffold
    setTimeout(() => {
      setSummary({
        total_requests: 125430,
        total_bytes: 104857600,
        unique_visitors: 4500
      });
      setLoading(false);
    }, 1000);
  }, []);

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-6">LogLens Dashboard</h1>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-xl">Loading analytics...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold mb-2 text-gray-400">Total Requests</h2>
            <p className="text-4xl font-bold text-blue-500">
              {summary?.total_requests.toLocaleString()}
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold mb-2 text-gray-400">Bandwidth</h2>
            <p className="text-4xl font-bold text-green-500">
              {(summary ? summary.total_bytes / (1024 * 1024) : 0).toFixed(2)} MB
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold mb-2 text-gray-400">Unique Visitors</h2>
            <p className="text-4xl font-bold text-purple-500">
              {summary?.unique_visitors.toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {/* Placeholder for charts */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg h-80 flex items-center justify-center">
          <p className="text-gray-500">Traffic Trend Chart (Placeholder)</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg h-80 flex items-center justify-center">
          <p className="text-gray-500">Status Code Distribution (Placeholder)</p>
        </div>
      </div>
    </div>
  );
}
