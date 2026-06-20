import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { ChartCard } from '../components/ui/ChartCard';
import { DataTable, type ColumnDef } from '../components/ui/DataTable';
import { LoadingState, ErrorState } from '../components/ui/States';
import { useFilterContext } from '../context/FilterContext';
import { fetchApi } from '../utils/api';

export function UrlAnalytics() {
  const { filters } = useFilterContext();
  const [urlsData, setUrlsData] = useState<any>(null);
  const [landingData, setLandingData] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [normalized, setNormalized] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [urls, landing] = await Promise.all([
        fetchApi<any>('/urls', filters, { limit: 15, normalized }),
        fetchApi<any>('/urls/landing-bounce', filters, { limit: 10 })
      ]);
      setUrlsData(urls);
      setLandingData(landing);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters, normalized]);

  if (loading && !urlsData) return <PageContainer title="URL Analytics"><LoadingState /></PageContainer>;
  if (error) return <PageContainer title="URL Analytics"><ErrorState error={error} retry={loadData} /></PageContainer>;

  const defaultColumns: ColumnDef<any>[] = [
    { header: 'URL', accessorKey: 'url' },
    { header: 'Count', accessorKey: 'count', className: 'text-right' }
  ];

  const actions = (
    <label className="flex items-center space-x-2 text-sm text-gray-300">
      <input
        type="checkbox"
        checked={normalized}
        onChange={(e) => setNormalized(e.target.checked)}
        className="rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
      />
      <span>Use Normalized URLs</span>
    </label>
  );

  return (
    <PageContainer title="URL Analytics" description="Discover your most popular, entry, and exit pages." actions={actions}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Top URLs">
          <DataTable data={urlsData?.top_urls || []} columns={defaultColumns} keyExtractor={(r) => r.url} />
        </ChartCard>

        <ChartCard title="Landing Pages">
          <DataTable data={landingData?.landing_pages || []} columns={defaultColumns} keyExtractor={(r) => r.url} />
        </ChartCard>

        <ChartCard title="Entry Pages">
          <DataTable data={urlsData?.entry_pages || []} columns={defaultColumns} keyExtractor={(r) => r.url} />
        </ChartCard>

        <ChartCard title="Exit Pages">
          <DataTable data={urlsData?.exit_pages || []} columns={defaultColumns} keyExtractor={(r) => r.url} />
        </ChartCard>
      </div>
    </PageContainer>
  );
}
