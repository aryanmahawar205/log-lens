import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { LoadingState, ErrorState } from '../components/ui/States';
import { fetchApi } from '../utils/api';
import { Cpu, Terminal, Clock, Server, CheckCircle, XCircle, Shield, FileText, FolderOpen } from 'lucide-react';
import { useFilterContext } from '../context/FilterContext';

export function SystemDiagnostics() {
  const { filters } = useFilterContext();
  const [provider, setProvider] = useState<any>(null);
  const [goaccessDiag, setGoaccessDiag] = useState<any>(null);
  const [sigmaDiag, setSigmaDiag] = useState<any>(null);
  const [sigmaRules, setSigmaRules] = useState<any[]>([]);
  const [folderScans, setFolderScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [provRes, diagRes, sigmaRes, rulesRes, folderScansRes] = await Promise.all([
        fetchApi<any>('/system/provider'),
        fetchApi<any>('/system/integrations/goaccess', filters),
        fetchApi<any>('/system/integrations/sigma'),
        fetchApi<any[]>('/security/rules'),
        fetchApi<any[]>('/system/folder-scans')
      ]);
      setProvider(provRes);
      setGoaccessDiag(diagRes);
      setSigmaDiag(sigmaRes);
      setSigmaRules(rulesRes || []);
      setFolderScans(folderScansRes || []);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const filteredRules = sigmaRules.filter(rule =>
    rule.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.filename?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
              <span className="text-gray-500">Total Discovered</span>
              <span className="font-medium text-gray-200">{sigmaDiag?.total_discovered_rules ?? 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Loaded Rules</span>
              <span className="font-medium text-emerald-400">{sigmaDiag?.loaded_rules ?? 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Failed / Ignored</span>
              <span className="font-medium text-rose-400">{(sigmaDiag?.failed_rules || 0)} / {(sigmaDiag?.ignored_rules || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Duplicates (Ignored)</span>
              <span className="font-medium text-amber-400">{sigmaDiag?.duplicate_rules ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Directories Scanned</span>
              <span className="font-medium text-gray-200 flex items-center">
                <FolderOpen className="w-3 h-3 mr-1" /> {sigmaDiag?.directories_scanned ?? 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Reload Duration</span>
              <span className="font-medium text-gray-200">{sigmaDiag?.last_reload_duration !== undefined ? `${(sigmaDiag.last_reload_duration * 1000).toFixed(0)}ms` : 'N/A'}</span>
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
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center text-orange-400">
            <FileText className="w-5 h-5 mr-2" />
            <h3 className="font-semibold text-gray-200">Sigma Rule Inventory</h3>
          </div>
          <input
            type="text"
            placeholder="Search rules..."
            className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block px-3 py-1.5"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 bg-gray-800/50 uppercase border-b border-gray-800 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3">Filename</th>
                <th className="px-6 py-3">Rule Title</th>
                <th className="px-6 py-3">Rule ID</th>
                <th className="px-6 py-3">Severity</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Load State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {filteredRules.length > 0 ? (
                filteredRules.map((rule: any, idx: number) => {
                  return (
                    <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                      <td className="px-6 py-4 text-gray-300 whitespace-nowrap">
                        {rule.filename}
                      </td>
                      <td className="px-6 py-4 text-gray-200">{rule.title || 'Unknown Title'}</td>
                      <td className="px-6 py-4 text-gray-400 font-mono text-xs">{rule.id || 'N/A'}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          rule.level === 'critical' || rule.level === 'high' ? 'bg-rose-500/10 text-rose-400' :
                          rule.level === 'medium' ? 'bg-orange-500/10 text-orange-400' : 'bg-blue-500/10 text-blue-400'
                        }`}>
                          {rule.level?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-400 capitalize">{rule.status || 'experimental'}</td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400">
                          LOADED
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No rules loaded or matching search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden mb-6">
        <div className="p-4 border-b border-gray-800 flex items-center text-blue-400">
          <FolderOpen className="w-5 h-5 mr-2" />
          <h3 className="font-semibold text-gray-200">Folder Scan History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 bg-gray-800/50 uppercase border-b border-gray-800">
              <tr>
                <th className="px-6 py-3">Scan Time</th>
                <th className="px-6 py-3">Folder Path</th>
                <th className="px-6 py-3">Discovered</th>
                <th className="px-6 py-3">Imported</th>
                <th className="px-6 py-3">Skipped</th>
                <th className="px-6 py-3">Duration (s)</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {folderScans && folderScans.length > 0 ? (
                folderScans.map((scan: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                    <td className="px-6 py-4 text-gray-300 whitespace-nowrap">
                      {new Date(scan.scanned_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-gray-300 truncate max-w-[200px]" title={scan.folder_path}>
                      {scan.folder_path}
                    </td>
                    <td className="px-6 py-4 text-gray-300">
                      {scan.files_discovered}
                    </td>
                    <td className="px-6 py-4 text-emerald-400 font-medium">
                      {scan.files_imported}
                    </td>
                    <td className="px-6 py-4 text-yellow-400">
                      {scan.files_skipped}
                    </td>
                    <td className="px-6 py-4 text-gray-300">
                      {scan.duration_sec?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      {scan.status === 'SUCCESS' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-900/50 text-emerald-400">
                          SUCCESS
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">
                          {scan.status}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    No folder scans recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
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
