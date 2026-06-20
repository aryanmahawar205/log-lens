import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { LoadingState, ErrorState } from '../components/ui/States';
import { useFilterContext } from '../context/FilterContext';
import { fetchApi } from '../utils/api';
import { ArrowLeft, ArrowRight } from 'lucide-react';

export function LogExplorer() {
  const { filters, setFilter } = useFilterContext();
  const [logsData, setLogsData] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Pagination and sorting state
  const [page, setPage] = useState(1);
  const limit = 50;
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortDesc, setSortDesc] = useState(true);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = (page - 1) * limit;
      const data = await fetchApi<any>('/logs', filters, { limit, offset, sort_by: sortBy, sort_desc: sortDesc });
      setLogsData(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  // Reset page when filters or sorting changes
  useEffect(() => {
    setPage(1);
  }, [filters, sortBy, sortDesc]);

  // Load data when dependencies change
  useEffect(() => {
    loadData();
  }, [page, filters, sortBy, sortDesc]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(true); // Default to descending when changing columns
    }
  };

  const renderSortableHeader = (label: string, columnKey: string) => (
    <div
      className="flex items-center cursor-pointer hover:text-white transition-colors"
      onClick={() => handleSort(columnKey)}
    >
      {label}
      {sortBy === columnKey && (
        <span className="ml-1 text-blue-400 text-xs">
          {sortDesc ? '↓' : '↑'}
        </span>
      )}
    </div>
  );

  // Since our DataTable component expects string headers, let's just build a custom table here for the explorer
  // to properly support clickable sorting headers.

  return (
    <PageContainer title="Log Explorer" description="Search, filter, sort, and paginate through your raw log entries.">

      {error && <ErrorState error={error} retry={loadData} />}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden flex flex-col min-h-[600px]">
        {/* Toolbar */}
        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/30">
          <div className="text-sm text-gray-400">
            {loading ? 'Loading...' : `Showing ${(page - 1) * limit + 1} - ${Math.min(page * limit, logsData?.total || 0)} of ${logsData?.total?.toLocaleString() || 0} entries`}
          </div>

          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Search User Agents..."
              value={filters.user_agent || ''}
              onChange={(e) => setFilter('user_agent', e.target.value)}
              className="bg-gray-800 border border-gray-700 text-sm rounded px-3 py-1.5 text-white outline-none focus:border-blue-500 min-w-[250px]"
            />
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
              className="p-1.5 rounded bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-300 min-w-[3rem] text-center">
              Page {page}
            </span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!logsData || logsData.logs.length < limit || loading}
              className="p-1.5 rounded bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Table Area */}
        <div className="flex-1 overflow-x-auto relative">
          {loading && (
             <div className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm z-10 flex items-center justify-center">
               <LoadingState message="Fetching logs..." />
             </div>
          )}

          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="text-xs text-gray-400 bg-gray-900 uppercase sticky top-0 z-0 border-b border-gray-800">
              <tr>
                <th className="px-4 py-3 font-medium w-48">{renderSortableHeader('Timestamp', 'timestamp')}</th>
                <th className="px-4 py-3 font-medium w-32">{renderSortableHeader('IP', 'ip')}</th>
                <th className="px-4 py-3 font-medium w-24">{renderSortableHeader('Method', 'method')}</th>
                <th className="px-4 py-3 font-medium w-24">{renderSortableHeader('Status', 'status_code')}</th>
                <th className="px-4 py-3 font-medium">{renderSortableHeader('URL', 'url')}</th>
                <th className="px-4 py-3 font-medium text-right w-32">{renderSortableHeader('Time (ms)', 'response_time_ms')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {!logsData?.logs?.length && !loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                    No log entries found matching the current filters.
                  </td>
                </tr>
              ) : (
                logsData?.logs.map((row: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-800/30 transition-colors font-mono text-[13px]">
                    <td className="px-4 py-2.5 text-gray-400">{new Date(row.timestamp).toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-gray-300">{row.ip}</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded font-sans text-xs font-medium ${
                        row.method === 'GET' ? 'bg-blue-500/10 text-blue-400' :
                        row.method === 'POST' ? 'bg-emerald-500/10 text-emerald-400' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {row.method}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded font-sans text-xs font-medium ${
                        row.status_code >= 500 ? 'bg-rose-500/10 text-rose-400' :
                        row.status_code >= 400 ? 'bg-amber-500/10 text-amber-400' :
                        row.status_code >= 300 ? 'bg-purple-500/10 text-purple-400' :
                        'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        {row.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-300 truncate max-w-xs md:max-w-md lg:max-w-xl" title={row.url}>{row.url}</td>
                    <td className="px-4 py-2.5 text-right text-gray-500">{row.response_time_ms ? `${Math.round(row.response_time_ms)}ms` : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
