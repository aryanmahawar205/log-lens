import { useState, useEffect } from 'react';
import { useFilterContext } from '../context/FilterContext';
import { useDatasetContext } from '../context/DatasetContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { AlertTriangle, Shield, ShieldAlert } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchApi } from '../utils/api';

export function SecurityAnalytics() {
  const { filters } = useFilterContext();
  const { selectedDataset } = useDatasetContext();
  if (!selectedDataset) return null;
  const [overview, setOverview] = useState<any>(null);
  const [findings, setFindings] = useState<any[]>([]);
  const [attackTrends, setAttackTrends] = useState<any[]>([]);
  const [suspiciousIps, setSuspiciousIps] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ovData, finData, trData, ipData] = await Promise.all([
          fetchApi<any>('/security/overview', filters),
          fetchApi<any[]>('/security/findings', filters),
          fetchApi<any[]>('/security/attack-trends', filters),
          fetchApi<any[]>('/security/suspicious-ips', filters)
        ]);

        setOverview(ovData || {});
        setFindings(finData || []);
        setAttackTrends(trData || []);
        setSuspiciousIps(ipData || []);
      } catch (error) {
        console.error('Failed to fetch security analytics:', error);
      }
    };

    fetchData();
  }, [filters, selectedDataset]);

  const COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6'
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100 mb-6 flex items-center">
        <Shield className="mr-3 text-red-500" /> Security Analytics
      </h1>

      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-400">Total Attacks</p>
                  <h3 className="text-2xl font-bold text-red-400 mt-1">{overview.total_attacks}</h3>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500/50" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-400">Suspicious IPs</p>
                  <h3 className="text-2xl font-bold text-orange-400 mt-1">{overview.suspicious_ips_count}</h3>
                </div>
                <ShieldAlert className="w-8 h-8 text-orange-500/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="col-span-1 lg:col-span-2">
             <CardContent className="p-6 h-32 flex flex-col justify-center">
                 <p className="text-sm font-medium text-gray-400 mb-2">Severity Distribution</p>
                 <div className="flex space-x-4">
                     {overview.severity_distribution?.map((sev: any) => (
                         <div key={sev.name} className="flex flex-col items-center">
                             <span className="text-lg font-bold" style={{color: COLORS[sev.name as keyof typeof COLORS]}}>{sev.value}</span>
                             <span className="text-xs text-gray-500 uppercase">{sev.name}</span>
                         </div>
                     ))}
                     {(!overview.severity_distribution || overview.severity_distribution.length === 0) && (
                        <span className="text-gray-500">No attacks detected</span>
                     )}
                 </div>
             </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Attack Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={attackTrends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="timestamp" stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
                  <YAxis stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#f3f4f6' }}
                    itemStyle={{ color: '#ef4444' }}
                  />
                  <Line type="monotone" dataKey="attacks" stroke="#ef4444" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Attack Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overview?.attack_categories || []} layout="vertical" margin={{ left: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                  <XAxis type="number" stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
                  <YAxis dataKey="name" type="category" stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#f3f4f6' }}
                    itemStyle={{ color: '#ef4444' }}
                  />
                  <Bar dataKey="value" fill="#f97316" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Suspicious IPs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-400 uppercase bg-gray-900 border-b border-gray-800">
                <tr>
                  <th className="px-4 py-3">IP Address</th>
                  <th className="px-4 py-3">Risk Score</th>
                  <th className="px-4 py-3">Class</th>
                  <th className="px-4 py-3">Signatures</th>
                  <th className="px-4 py-3">Critical Findings</th>
                </tr>
              </thead>
              <tbody>
                {suspiciousIps.map((ip, idx) => (
                  <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-medium text-gray-200">{ip.ip}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-700 rounded-full h-2 mr-2">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${ip.score}%`,
                              backgroundColor: COLORS[ip.classification as keyof typeof COLORS] || COLORS.low
                            }}
                          ></div>
                        </div>
                        <span className="text-gray-300">{ip.score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded text-xs font-semibold" style={{
                        backgroundColor: `${(COLORS[ip.classification as keyof typeof COLORS] || '#6b7280')}20`,
                        color: COLORS[ip.classification as keyof typeof COLORS] || '#6b7280'
                        }}>
                          {(ip.classification ?? 'unknown').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {(ip.attack_signatures ?? []).join(', ')}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {ip.critical_count}
                    </td>
                  </tr>
                ))}
                {suspiciousIps.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                      No suspicious IPs detected.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Findings Explorer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {findings.slice(0, 20).map((finding, idx) => (
              <div key={idx} className="p-4 rounded-lg border border-gray-800 bg-gray-900/50 flex flex-col md:flex-row gap-4">
                <div className="w-32 flex flex-col justify-center items-center p-2 rounded bg-gray-950 border border-gray-800">
                  <AlertTriangle className="w-6 h-6 mb-1" style={{color: COLORS[finding.severity as keyof typeof COLORS]}} />
                  <span className="text-xs font-bold uppercase" style={{color: COLORS[finding.severity as keyof typeof COLORS]}}>{finding.severity}</span>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                        <h4 className="font-bold text-gray-200 capitalize">{(finding.rule_title ?? finding.type ?? 'unknown').replace('_', ' ')}</h4>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${finding.sigma_source ? 'border-purple-500/50 text-purple-400 bg-purple-500/10' : 'border-blue-500/50 text-blue-400 bg-blue-500/10'}`}>
                            {finding.sigma_source ? 'SIGMA' : 'CUSTOM'}
                        </span>
                    </div>
                    <span className="text-xs font-mono bg-gray-800 px-2 py-1 rounded text-gray-300">IP: {finding.ip}</span>
                  </div>
                  <div className="mt-2 text-sm text-gray-400">
                    <p className="font-semibold text-gray-300 mb-1">Evidence:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      {(finding.evidence ?? []).map((ev: string, i: number) => (
                        <li key={i} className="font-mono text-xs break-all">{ev}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
            {findings.length > 20 && (
              <p className="text-center text-sm text-gray-500 pt-4">Showing 20 of {findings.length} findings</p>
            )}
            {findings.length === 0 && (
              <p className="text-center text-gray-500 py-8">No security findings in the current timeframe.</p>
            )}
          </div>
        </CardContent>
      </Card>

    </div>
  );
}
