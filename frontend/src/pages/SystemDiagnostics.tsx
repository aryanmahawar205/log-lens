import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { LoadingState, ErrorState } from '../components/ui/States';
import { fetchApi } from '../utils/api';
import { Cpu, Terminal, Clock, Server, CheckCircle, XCircle, Shield } from 'lucide-react';
import { useFilterContext } from '../context/FilterContext';

export function SystemDiagnostics() {
  const { filters } = useFilterContext();
  const [provider, setProvider] = useState<any>(null);
  const [goaccessDiag, setGoaccessDiag] = useState<any>(null);
  const [sigmaDiag, setSigmaDiag] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [provRes, diagRes, sigmaRes] = await Promise.all([
        fetchApi<any>('/system/provider'),
        fetchApi<any>('/system/integrations/goaccess', filters),
        fetchApi<any>('/system/integrations/sigma')
      ]);
      setProvider(provRes);
      setGoaccessDiag(diagRes);
      setSigmaDiag(sigmaRes);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  if (loading && !provider) return <PageContainer title="System Diagnostics"><LoadingState /></PageContainer>;
  if (error) return <PageContainer title="System Diagnostics"><ErrorState error={error} retry={loadData} /></PageContainer>;

  return (
    <PageContainer title="System Diagnostics" description="View system integration status and analytics provider metrics.">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4 text-blue-400">
            <Server className="w-5 h-5 mr-2" />
            <h3 className="font-semibold text-gray-200">Active Provider</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Current</span>
              <span className="font-medium text-gray-200 uppercase">{provider?.active_provider}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Fallback</span>
              <span className="font-medium text-gray-200 uppercase">{provider?.fallback_provider}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4 text-emerald-400">
            <Cpu className="w-5 h-5 mr-2" />
            <h3 className="font-semibold text-gray-200">GoAccess Status</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Available</span>
              <span className="font-medium flex items-center">
                {provider?.goaccess_available ? (
                  <><CheckCircle className="w-4 h-4 mr-1 text-emerald-400" /><span className="text-emerald-400">Yes</span></>
                ) : (
                  <><XCircle className="w-4 h-4 mr-1 text-rose-400" /><span className="text-rose-400">No</span></>
                )}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Version</span>
              <span className="font-medium text-gray-200">{provider?.goaccess_version || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4 text-purple-400">
            <Clock className="w-5 h-5 mr-2" />
            <h3 className="font-semibold text-gray-200">Execution Metrics</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Last Status</span>
              <span className={`font-medium ${provider?.last_execution_status === 'success' ? 'text-emerald-400' : provider?.last_execution_status === 'failed' ? 'text-rose-400' : 'text-gray-400'}`}>
                {provider?.last_execution_status ? provider.last_execution_status.toUpperCase() : 'UNKNOWN'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Duration</span>
              <span className="font-medium text-gray-200">{provider?.duration ? `${(provider.duration * 1000).toFixed(0)}ms` : 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center text-orange-400">
              <Shield className="w-5 h-5 mr-2" />
              <h3 className="font-semibold text-gray-200">Sigma Engine</h3>
            </div>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                sigmaDiag?.provider_status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
              }`}>
                {sigmaDiag?.provider_status?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Healthy</span>
              <span className="font-medium flex items-center">
                {sigmaDiag?.healthy_state ? (
                  <><CheckCircle className="w-4 h-4 mr-1 text-emerald-400" /><span className="text-emerald-400">Yes</span></>
                ) : (
                  <><XCircle className="w-4 h-4 mr-1 text-rose-400" /><span className="text-rose-400">No</span></>
                )}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Loaded Rules</span>
              <span className="font-medium text-gray-200">{sigmaDiag?.loaded_rules ?? 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Failed/Ignored</span>
              <span className="font-medium text-gray-200">{(sigmaDiag?.failed_rules || 0)} / {(sigmaDiag?.ignored_rules || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Reload</span>
              <span className="font-medium text-gray-400 text-sm">{sigmaDiag?.last_reload ? new Date(sigmaDiag.last_reload).toLocaleString() : 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4 text-purple-400">
            <Terminal className="w-5 h-5 mr-2" />
            <h3 className="font-semibold text-gray-200">Sigma Execution</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Execution Count</span>
              <span className="font-medium text-gray-200">{sigmaDiag?.execution_count ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Duration</span>
              <span className="font-medium text-gray-200">{sigmaDiag?.execution_duration !== undefined ? `${(sigmaDiag.execution_duration * 1000).toFixed(0)}ms` : 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Executed</span>
              <span className="font-medium text-gray-400 text-sm">{sigmaDiag?.last_execution_timestamp ? new Date(sigmaDiag.last_execution_timestamp).toLocaleString() : 'N/A'}</span>
            </div>
            {sigmaDiag?.last_error && (
              <div className="mt-2 text-xs text-rose-400 bg-rose-500/10 p-2 rounded break-words">
                {sigmaDiag.last_error}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden mb-6">
        <div className="p-4 border-b border-gray-800 flex items-center text-blue-400">
          <Terminal className="w-5 h-5 mr-2" />
          <h3 className="font-semibold text-gray-200">GoAccess Execution History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 bg-gray-800/50 uppercase border-b border-gray-800">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Upload ID</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Duration</th>
                <th className="px-6 py-3">Version</th>
                <th className="px-6 py-3 text-right">Reports</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {goaccessDiag?.execution_history?.length > 0 ? (
                goaccessDiag.execution_history.map((exec: any, idx: number) => {
                  const artifacts = typeof exec.artifacts === 'string' ? JSON.parse(exec.artifacts) : exec.artifacts;
                  return (
                    <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                      <td className="px-6 py-4 text-gray-300 whitespace-nowrap">
                        {new Date(exec.execution_timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-gray-400 font-mono text-xs">{exec.upload_id === 0 ? 'Global' : exec.upload_id}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          exec.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                        }`}>
                          {exec.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-300">{exec.duration_sec ? `${(exec.duration_sec * 1000).toFixed(0)}ms` : '-'}</td>
                      <td className="px-6 py-4 text-gray-400">{exec.version}</td>
                      <td className="px-6 py-4 text-right">
                        {exec.status === 'success' && artifacts?.html && (
                          <a
                            href={`/api/v1/system/integrations/goaccess/report?path=${encodeURIComponent(artifacts.html)}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-400 hover:text-blue-300 text-xs flex items-center justify-end"
                          >
                            View HTML
                          </a>
                        )}
                        {exec.status === 'failed' && artifacts?.error && (
                          <span className="text-xs text-rose-400 max-w-[200px] truncate block" title={artifacts.error}>{artifacts.error}</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No execution history found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
