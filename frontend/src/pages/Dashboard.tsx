import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { MetricCard } from '../components/ui/MetricCard';
import { LoadingState, ErrorState } from '../components/ui/States';
import { useFilterContext } from '../context/FilterContext';
import { useDatasetContext } from '../context/DatasetContext';
import { fetchApi } from '../utils/api';
import { Activity, Users, Globe, HardDrive, Clock, AlertTriangle, FileText, CheckCircle, Database, Cpu, Terminal, ShieldCheck, XCircle } from 'lucide-react';

interface ProviderInfo {
  active_provider: string;
  fallback_provider: string;
  goaccess_available: boolean;
  last_execution: string | null;
  last_execution_status: string | null;
  goaccess_version: string | null;
  duration: number | null;
}

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
  const { selectedDataset } = useDatasetContext();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [provider, setProvider] = useState<ProviderInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, providerData] = await Promise.all([
        fetchApi<DashboardSummary>('/overview', filters),
        fetchApi<ProviderInfo>('/system/provider')
      ]);
      setSummary(summaryData);
      setProvider(providerData);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  // Layout handles empty state (0 datasets), so it's safe to render global

  if (loading && !summary) return <PageContainer title="Dashboard"><LoadingState message="Loading dashboard overview..." /></PageContainer>;
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

  const errorRate = summary && summary.total_requests > 0
    ? ((summary.total_requests - summary.hits) / summary.total_requests * 100).toFixed(2)
    : '0.00';

  return (
    <PageContainer title="Dashboard" description="High-level overview of your web traffic and analytics.">

      {/* Dataset Details Panel */}
      {selectedDataset ? (
        <div className="mb-6 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between">
          <div className="flex items-center mb-4 md:mb-0">
            <div className="p-3 bg-blue-500/10 rounded-lg mr-4 border border-blue-500/20">
              <FileText className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{selectedDataset.filename}</h3>
              <p className="text-sm text-gray-400 flex items-center mt-1">
                <Database className="w-3.5 h-3.5 mr-1" />
                Uploaded on {new Date(selectedDataset.uploaded_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 md:gap-8">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Format</p>
              <p className="font-medium text-gray-200">{selectedDataset.format}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Parser</p>
              <p className="font-medium text-gray-200">{selectedDataset.parser_used}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Confidence</p>
              <p className="font-medium text-emerald-400 flex items-center">
                {Math.round(selectedDataset.confidence * 100)}%
                <CheckCircle className="w-3.5 h-3.5 ml-1" />
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Entries</p>
              <p className="font-medium text-blue-400">{selectedDataset.total_entries.toLocaleString()}</p>
            </div>
            {provider && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Provider</p>
                <p className={`font-medium flex items-center ${provider.active_provider === 'goaccess' ? 'text-orange-400' : 'text-blue-400'}`}>
                  <Cpu className="w-3.5 h-3.5 mr-1" />
                  {provider.active_provider === 'goaccess' ? 'GoAccess' : 'Native'}
                  {provider.active_provider === 'goaccess' && provider.last_execution_status === 'failed' && (
                    <span className="ml-1 text-[10px] bg-red-500/20 text-red-400 px-1 rounded border border-red-500/30">FALLBACK</span>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="mb-6 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between">
          <div className="flex items-center mb-4 md:mb-0">
            <div className="p-3 bg-blue-500/10 rounded-lg mr-4 border border-blue-500/20">
              <Globe className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Global Analytics</h3>
              <p className="text-sm text-gray-400 flex items-center mt-1">
                Aggregated metrics across all datasets
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
            {provider && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Provider</p>
                <p className={`font-medium flex items-center ${provider.active_provider === 'goaccess' ? 'text-orange-400' : 'text-blue-400'}`}>
                  <Cpu className="w-3.5 h-3.5 mr-1" />
                  {provider.active_provider === 'goaccess' ? 'GoAccess' : 'Native'}
                  {provider.active_provider === 'goaccess' && provider.last_execution_status === 'failed' && (
                    <span className="ml-1 text-[10px] bg-red-500/20 text-red-400 px-1 rounded border border-red-500/30">FALLBACK</span>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Requests"
          value={(summary?.total_requests ?? 0).toLocaleString()}
          icon={Activity}
          valueColor="text-blue-400"
        />
        <MetricCard
          title="Unique Visitors"
          value={(summary?.unique_visitors ?? 0).toLocaleString()}
          icon={Users}
          valueColor="text-emerald-400"
        />
        <MetricCard
          title="Sessions"
          value={(summary?.total_sessions ?? 0).toLocaleString()}
          icon={Globe}
          valueColor="text-purple-400"
        />
        <MetricCard
          title="Bandwidth"
          value={formatBytes(summary?.total_bytes ?? 0)}
          icon={HardDrive}
          valueColor="text-orange-400"
        />
        <MetricCard
          title="Avg Session Duration"
          value={`${Math.round(summary?.avg_session_duration_sec ?? 0)}s`}
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 p-6 rounded-xl flex flex-col items-center justify-center min-h-[300px]">
           <p className="text-gray-500 text-sm">Detailed traffic and visitor charts available in the specialized tabs.</p>
           <div className="flex gap-4 mt-4">
              <div className="h-2 w-24 bg-gray-800 rounded-full animate-pulse"></div>
              <div className="h-2 w-32 bg-gray-800 rounded-full animate-pulse"></div>
           </div>
        </div>

        {/* Diagnostics Panel */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-gray-200 flex items-center">
              <Terminal className="w-4 h-4 mr-2 text-blue-400" />
              Diagnostics
            </h3>
            {provider?.active_provider === 'goaccess' ? (
              <span className="text-[10px] bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded-full border border-orange-500/20 uppercase font-bold tracking-tighter">External</span>
            ) : (
              <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20 uppercase font-bold tracking-tighter">Internal</span>
            )}
          </div>

          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Analytics Provider</span>
              <span className="text-gray-200 font-medium">{provider?.active_provider === 'goaccess' ? 'GoAccess' : 'Native'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Version</span>
              <span className="text-gray-200 font-medium">{provider?.active_provider === 'goaccess' ? (provider?.goaccess_version || 'Unknown') : 'v1.0.0 (Native)'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Status</span>
              <div className="flex items-center font-medium">
                {provider?.last_execution_status === 'success' ? (
                  <><ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" /><span className="text-emerald-400">Success</span></>
                ) : provider?.last_execution_status === 'failed' ? (
                  <><XCircle className="w-3.5 h-3.5 mr-1 text-rose-400" /><span className="text-rose-400">Fallback Active</span></>
                ) : (
                  <span className="text-gray-400">No data</span>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Processing Time</span>
              <span className="text-gray-200 font-medium">{provider?.duration ? `${(provider.duration * 1000).toFixed(0)}ms` : 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Last Ran</span>
              <span className="text-gray-400 text-xs truncate max-w-[120px]">
                {provider?.last_execution ? new Date(provider.last_execution).toLocaleTimeString() : 'Never'}
              </span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-800">
             <p className="text-[10px] text-gray-600 italic">
               Verification: Data sourced from {provider?.active_provider === 'goaccess' && provider?.last_execution_status === 'success' ? 'external binary artifacts' : 'internal DuckDB OLAP engine'}.
             </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
