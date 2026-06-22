import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { MetricCard } from '../components/ui/MetricCard';
import { LoadingState, ErrorState } from '../components/ui/States';
import { useFilterContext } from '../context/FilterContext';
import { fetchApi } from '../utils/api';
import { Activity, Users, Globe, HardDrive, Clock, AlertTriangle } from 'lucide-react';

// interface DashboardSummary {
//   total_requests: number;
//   hits: number;
//   unique_visitors: number;
//   sessions: number;
//   returning_visitors: number;
//   pages_per_session: number;
//   avg_session_duration_sec: number;
//   total_bytes: number;
//   error_rate?: number; // Might need calculation
// }

interface DashboardSummary {
  total_requests: number;
  hits: number;
  unique_visitors: number;
  total_sessions: number;
  returning_visitors: number;
  avg_pages_per_session: number;
  avg_session_duration_sec: number;
  total_bytes: number;
}

export function Dashboard() {
  const { filters } = useFilterContext();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<DashboardSummary>('/overview', filters);
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  if (loading) return <PageContainer title="Dashboard"><LoadingState message="Loading dashboard overview..." /></PageContainer>;
  if (error) return <PageContainer title="Dashboard"><ErrorState error={error} retry={loadData} /></PageContainer>;
  if (!summary) return <PageContainer title="Dashboard"><div className="text-gray-400">No data available</div></PageContainer>;

  // Format bytes to MB/GB
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const errorRate = summary.total_requests > 0
    ? ((summary.total_requests - summary.hits) / summary.total_requests * 100).toFixed(2)
    : '0.00';

  return (
    <PageContainer title="Dashboard" description="High-level overview of your web traffic and analytics.">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Requests"
          value={(summary.total_requests ?? 0).toLocaleString()}
          icon={Activity}
          valueColor="text-blue-400"
        />
        <MetricCard
          title="Unique Visitors"
          value={(summary.unique_visitors ?? 0).toLocaleString()}
          icon={Users}
          valueColor="text-emerald-400"
        />
        <MetricCard
          title="Sessions"
          value={(summary.total_sessions ?? 0).toLocaleString()}
          icon={Globe}
          valueColor="text-purple-400"
        />
        <MetricCard
          title="Bandwidth"
          value={formatBytes(summary.total_bytes ?? 0)}
          icon={HardDrive}
          valueColor="text-orange-400"
        />
        <MetricCard
          title="Avg Session Duration"
          value={`${Math.round(summary.avg_session_duration_sec ?? 0)}s`}
          icon={Clock}
          valueColor="text-teal-400"
        />
        <MetricCard
          title="Error Rate"
          value={`${errorRate}%`}
          icon={AlertTriangle}
          valueColor="text-rose-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl flex items-center justify-center min-h-[300px]">
           <p className="text-gray-500 text-sm">Detailed traffic charts available in the Traffic tab.</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl flex items-center justify-center min-h-[300px]">
           <p className="text-gray-500 text-sm">Detailed visitor charts available in the Visitors tab.</p>
        </div>
      </div>
    </PageContainer>
  );
}
