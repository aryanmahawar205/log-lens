import { useState, useEffect } from 'react';
import { PageContainer } from '../components/ui/PageContainer';
import { ChartCard } from '../components/ui/ChartCard';
import { LoadingState, ErrorState } from '../components/ui/States';
import { CustomLineChart } from '../components/charts/CustomLineChart';
import { CustomBarChart } from '../components/charts/CustomBarChart';
import { useFilterContext } from '../context/FilterContext';
import { fetchApi } from '../utils/api';

export function TrafficAnalytics() {
  const { filters } = useFilterContext();
  const [resolution, setResolution] = useState('hour');

  const [timeData, setTimeData] = useState<any[]>([]);
  const [trendsData, setTrendsData] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [timeRes, trendsRes] = await Promise.all([
        fetchApi<any[]>('/traffic', filters, { resolution }),
        fetchApi<any>('/traffic/trends', filters)
      ]);
      setTimeData(timeRes);
      setTrendsData(trendsRes);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters, resolution]);

  if (loading && timeData.length === 0) return <PageContainer title="Traffic Analytics"><LoadingState /></PageContainer>;
  if (error) return <PageContainer title="Traffic Analytics"><ErrorState error={error} retry={loadData} /></PageContainer>;

  const formatTimeBucket = (bucket: string) => {
    const d = new Date(bucket);
    if (resolution === 'hour') return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (resolution === 'day') return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    return bucket;
  };

  const formattedTimeData = timeData.map(d => ({
    ...d,
    time_bucket: formatTimeBucket(d.time_bucket)
  }));

  const resolutionSelector = (
    <select
      value={resolution}
      onChange={(e) => setResolution(e.target.value)}
      className="bg-gray-800 border border-gray-700 text-sm rounded px-2 py-1 text-gray-300 outline-none"
    >
      <option value="minute">Minute</option>
      <option value="hour">Hour</option>
      <option value="day">Day</option>
    </select>
  );

  return (
    <PageContainer title="Traffic Analytics" description="Analyze request volume and traffic trends over time.">
      <div className="grid grid-cols-1 gap-6">
        <ChartCard title="Requests Over Time" action={resolutionSelector}>
          <CustomLineChart
            data={formattedTimeData}
            xDataKey="time_bucket"
            yDataKey="total_requests"
            colors={['#3b82f6']}
          />
        </ChartCard>

        <ChartCard title="Bandwidth Usage (Bytes)">
          <CustomLineChart
            data={formattedTimeData}
            xDataKey="time_bucket"
            yDataKey="total_bytes"
            colors={['#f59e0b']}
          />
        </ChartCard>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
           <ChartCard title="Peak Hours">
             <CustomBarChart
               data={trendsData?.peak_hours || []}
               xDataKey="hour"
               yDataKey="count"
               colors={['#10b981']}
             />
           </ChartCard>

           <ChartCard title="7-Day Moving Average (Requests)">
             <CustomLineChart
               data={(trendsData?.moving_averages || []).map((d: any) => ({
                 day: new Date(d.day).toLocaleDateString([], { month: 'short', day: 'numeric' }),
                 avg: Math.round(d.moving_avg_7d)
               }))}
               xDataKey="day"
               yDataKey="avg"
               colors={['#8b5cf6']}
             />
           </ChartCard>
        </div>
      </div>
    </PageContainer>
  );
}
