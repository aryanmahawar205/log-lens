import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { ChartCard } from '../components/ui/ChartCard';
import { MetricCard } from '../components/ui/MetricCard';
import { DataTable, type ColumnDef } from '../components/ui/DataTable';
import { LoadingState, ErrorState } from '../components/ui/States';
import { CustomLineChart } from '../components/charts/CustomLineChart';
import { useFilterContext } from '../context/FilterContext';
import { useDatasetContext } from '../context/DatasetContext';
import { fetchApi } from '../utils/api';
import { Clock, Zap } from 'lucide-react';

export function PerformanceAnalytics() {
  const { filters } = useFilterContext();
  const [metrics, setMetrics] = useState<any>(null);
  const [extended, setExtended] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [perfRes, extRes] = await Promise.all([
        fetchApi<any>('/performance', filters),
        fetchApi<any>('/performance/extended', filters)
      ]);
      setMetrics(perfRes);
      setExtended(extRes);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  if (loading && !metrics) return <PageContainer title="Performance Analytics"><LoadingState /></PageContainer>;
  if (error) return <PageContainer title="Performance"><ErrorState error={error} retry={loadData} /></PageContainer>;

  const slowEndpointsColumns: ColumnDef<any>[] = [
    { header: 'URL', accessorKey: 'url' },
    { header: 'Avg Time (ms)', cell: (row) => <span className="text-rose-400 font-medium">{Math.round(row.avg_time)}ms</span> },
    { header: 'Samples', accessorKey: 'count' }
  ];

  const formatMs = (val: number) => val ? `${Math.round(val)}ms` : 'N/A';

  return (
    <PageContainer title="Performance Analytics" description="Monitor application latency, slow endpoints, and throughput.">

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard title="Average Latency" value={formatMs(metrics?.avg_response_time)} icon={Clock} valueColor="text-blue-400" />
        <MetricCard title="P90 Latency" value={formatMs(metrics?.p90_response_time)} icon={Clock} valueColor="text-amber-400" />
        <MetricCard title="P95 Latency" value={formatMs(metrics?.p95_response_time)} icon={Clock} valueColor="text-orange-400" />
        <MetricCard title="P99 Latency" value={formatMs(metrics?.p99_response_time)} icon={Zap} valueColor="text-rose-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard title="Slowest Endpoints">
          <DataTable
            data={metrics?.slowest_endpoints || []}
            columns={slowEndpointsColumns}
            keyExtractor={(row) => row?.url || 'unknown'}
          />
        </ChartCard>

        <ChartCard title="Throughput (Bytes/sec)">
          <CustomLineChart
            data={(extended?.throughput_analysis || []).map((d: any) => ({
              time: new Date(d.hour_bucket).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              bps: Math.round(d.bytes_per_second)
            }))}
            xDataKey="time"
            yDataKey="bps"
            colors={['#10b981']}
          />
        </ChartCard>
      </div>
    </PageContainer>
  );
}
