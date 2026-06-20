import { type ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function ChartCard({ title, description, children, action, className = '' }: ChartCardProps) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl shadow-sm flex flex-col ${className}`}>
      <div className="flex justify-between items-center p-5 border-b border-gray-800/50">
        <div>
          <h3 className="text-base font-semibold text-gray-100">{title}</h3>
          {description && <p className="text-xs text-gray-400 mt-0.5">{description}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-5 flex-1 min-h-0">
        {children}
      </div>
    </div>
  );
}
