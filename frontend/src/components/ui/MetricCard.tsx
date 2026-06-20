import { DivideIcon as LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
    label?: string;
  };
  icon?: typeof LucideIcon;
  valueColor?: string;
}

export function MetricCard({ title, value, subtitle, trend, icon: Icon, valueColor = 'text-white' }: MetricCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        {Icon && <Icon className="w-4 h-4 text-gray-500" />}
      </div>

      <div className="flex items-baseline space-x-2">
        <span className={`text-2xl font-bold tracking-tight ${valueColor}`}>
          {value}
        </span>
        {subtitle && (
          <span className="text-xs text-gray-500 font-medium">
            {subtitle}
          </span>
        )}
      </div>

      {trend && (
        <div className="mt-3 flex items-center text-xs font-medium">
          <span className={trend.isPositive ? 'text-emerald-500' : 'text-rose-500'}>
            {trend.isPositive ? '+' : '-'}{Math.abs(trend.value)}%
          </span>
          <span className="text-gray-500 ml-2">{trend.label || 'vs previous'}</span>
        </div>
      )}
    </div>
  );
}
