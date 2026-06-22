import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { ChartCard } from '../components/ui/ChartCard';
import { DataTable, type ColumnDef } from '../components/ui/DataTable';
import { LoadingState, ErrorState } from '../components/ui/States';
import { CustomPieChart } from '../components/charts/CustomPieChart';
import { useFilterContext } from '../context/FilterContext';
import { useDatasetContext } from '../context/DatasetContext';
import { fetchApi } from '../utils/api';

export function VisitorAnalytics() {
  const { filters } = useFilterContext();
  const { selectedDataset } = useDatasetContext();
  if (!selectedDataset) return null;
  const [visitorData, setVisitorData] = useState<any>(null);
  const [extendedData, setExtendedData] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [visitors, extended] = await Promise.all([
        fetchApi<any>('/visitors', filters, { limit: 15 }),
        fetchApi<any>('/visitors/extended', filters)
      ]);
      setVisitorData(visitors);
      setExtendedData(extended);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters, selectedDataset]);

  if (loading && !visitorData) return <PageContainer title="Visitor Analytics"><LoadingState /></PageContainer>;
  if (error) return <PageContainer title="Visitor Analytics"><ErrorState error={error} retry={loadData} /></PageContainer>;

  const ipColumns: ColumnDef<any>[] = [
    { header: 'IP Address', accessorKey: 'ip' },
    { header: 'Requests', accessorKey: 'count', className: 'text-right' }
  ];

  const uaColumns: ColumnDef<any>[] = [
    { header: 'User Agent', accessorKey: 'user_agent', className: 'truncate max-w-md' },
    { header: 'Requests', accessorKey: 'count', className: 'text-right w-24' }
  ];

  return (
    <PageContainer title="Visitor Analytics" description="Analyze client IPs, user agents, browsers, and operating systems.">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ChartCard title="Browser Distribution">
          <CustomPieChart
            data={extendedData?.browser_distribution || []}
            nameKey="browser"
            dataKey="count"
          />
        </ChartCard>

        <ChartCard title="OS Distribution">
          <CustomPieChart
            data={extendedData?.os_distribution || []}
            nameKey="os"
            dataKey="count"
            colors={['#10b981', '#f59e0b', '#3b82f6', '#ec4899', '#8b5cf6']}
          />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Top IP Addresses">
          <DataTable data={visitorData?.top_ips || []} columns={ipColumns} keyExtractor={(r) => r.ip} />
        </ChartCard>

        <ChartCard title="Top User Agents">
          <DataTable data={visitorData?.top_user_agents || []} columns={uaColumns} keyExtractor={(r) => r.user_agent} />
        </ChartCard>
      </div>
    </PageContainer>
  );
}
