import { type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 rounded-lg bg-gray-900 border border-gray-800 h-full min-h-[200px]">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-4" />
      <p className="text-gray-400 text-sm font-medium">{message}</p>
    </div>
  );
}

export function ErrorState({ error, retry }: { error: Error | string; retry?: () => void }) {
  const errorMessage = typeof error === 'string' ? error : error.message;
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 rounded-lg bg-red-950/20 border border-red-900/50 min-h-[200px]">
      <div className="text-red-500 font-medium mb-2">Failed to load data</div>
      <p className="text-red-400/80 text-sm mb-4 text-center max-w-md">{errorMessage}</p>
      {retry && (
        <button
          onClick={retry}
          className="px-4 py-2 bg-red-900/40 hover:bg-red-900/60 text-red-200 text-sm rounded-md transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = 'No data available', icon }: { message?: string; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 rounded-lg bg-gray-900 border border-gray-800 min-h-[200px]">
      {icon && <div className="text-gray-500 mb-3">{icon}</div>}
      <p className="text-gray-400 text-sm font-medium">{message}</p>
    </div>
  );
}
