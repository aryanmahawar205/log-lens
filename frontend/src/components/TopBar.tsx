import { useState } from 'react';
import { Filter, Calendar, Globe, AlertCircle, Bot, X, UploadCloud, Database, Trash2 } from 'lucide-react';
import { useFilterContext } from '../context/FilterContext';
import { useDatasetContext } from '../context/DatasetContext';
import { FileUpload } from './FileUpload';

export function TopBar() {
  const { filters, setFilter, clearFilters, hasActiveFilters } = useFilterContext();
  const { datasets, selectedDataset, selectDataset, deleteDataset, refreshDatasets } = useDatasetContext();
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const handleDelete = async () => {
    if (selectedDataset && window.confirm('Are you sure you want to delete this dataset?')) {
      await deleteDataset(selectedDataset.id);
    }
  };

  return (
    <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 shrink-0 relative z-10">
      <div className="flex items-center">
        {datasets.length > 0 && (
          <div className="flex items-center bg-gray-800 rounded-md px-3 py-1.5 border border-gray-700">
            <Database className="w-4 h-4 text-blue-400 mr-2" />
            <select
              className="bg-transparent text-sm text-gray-200 outline-none w-48 truncate"
              value={selectedDataset?.id || ''}
              onChange={(e) => selectDataset(Number(e.target.value))}
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.filename} ({new Date(ds.uploaded_at).toLocaleDateString()}) - {ds.total_entries} entries
                </option>
              ))}
            </select>
            <button
              onClick={handleDelete}
              className="ml-2 text-gray-400 hover:text-red-400 transition-colors"
              title="Delete Dataset"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
        {selectedDataset && (
          <div className="ml-4 px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded-full border border-blue-800/50">
            Active: {selectedDataset.filename}
          </div>
        )}
      </div>

      <div className="flex items-center space-x-4">
        {hasActiveFilters() && (
          <button
            onClick={clearFilters}
            className="text-xs text-gray-400 hover:text-white flex items-center"
          >
            <X className="w-3 h-3 mr-1" />
            Clear Filters
          </button>
        )}

        <button
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className={`flex items-center px-3 py-1.5 rounded-md text-sm transition-colors ${
            hasActiveFilters() ? 'bg-blue-500 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters {hasActiveFilters() && '(Active)'}
        </button>

        <button
          onClick={() => setIsUploadOpen(true)}
          className="flex items-center px-3 py-1.5 rounded-md text-sm bg-teal-600 hover:bg-teal-500 text-white transition-colors"
        >
          <UploadCloud className="w-4 h-4 mr-2" />
          Upload Logs
        </button>
      </div>

      {/* Filter Dropdown */}
      {isFilterOpen && (
        <div className="absolute top-16 right-6 w-80 bg-gray-900 border border-gray-700 rounded-md shadow-xl p-4 mt-2">
          <div className="space-y-4">
            <div>
              <label className="flex items-center text-xs font-medium text-gray-400 mb-1.5">
                <Calendar className="w-3.5 h-3.5 mr-1" /> Date Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  value={filters.start_date || ''}
                  onChange={(e) => setFilter('start_date', e.target.value)}
                  className="bg-gray-800 border border-gray-700 text-sm rounded px-2 py-1.5 text-white outline-none focus:border-blue-500"
                />
                <input
                  type="date"
                  value={filters.end_date || ''}
                  onChange={(e) => setFilter('end_date', e.target.value)}
                  className="bg-gray-800 border border-gray-700 text-sm rounded px-2 py-1.5 text-white outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="flex items-center text-xs font-medium text-gray-400 mb-1.5">
                <Globe className="w-3.5 h-3.5 mr-1" /> IP Address
              </label>
              <input
                type="text"
                placeholder="e.g. 192.168.1.1"
                value={filters.ip || ''}
                onChange={(e) => setFilter('ip', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-sm rounded px-3 py-1.5 text-white outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center text-xs font-medium text-gray-400 mb-1.5">
                <Globe className="w-3.5 h-3.5 mr-1" /> URL Path
              </label>
              <input
                type="text"
                placeholder="e.g. /api/users"
                value={filters.url || ''}
                onChange={(e) => setFilter('url', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-sm rounded px-3 py-1.5 text-white outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center text-xs font-medium text-gray-400 mb-1.5">
                <AlertCircle className="w-3.5 h-3.5 mr-1" /> Status Code
              </label>
              <input
                type="number"
                placeholder="e.g. 404"
                value={filters.status_code || ''}
                onChange={(e) => setFilter('status_code', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full bg-gray-800 border border-gray-700 text-sm rounded px-3 py-1.5 text-white outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center text-xs font-medium text-gray-400 mb-1.5">
                <Bot className="w-3.5 h-3.5 mr-1" /> Bot Classification
              </label>
              <select
                value={filters.bot_classification || ''}
                onChange={(e) => setFilter('bot_classification', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-sm rounded px-3 py-1.5 text-white outline-none focus:border-blue-500"
              >
                <option value="">All Traffic</option>
                <option value="human">Human</option>
                <option value="bot">Bot</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-gray-800">
              <h2 className="text-lg font-semibold text-white">Upload Log File</h2>
              <button onClick={() => setIsUploadOpen(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <FileUpload onSuccess={async () => {
                await refreshDatasets();
                setTimeout(() => setIsUploadOpen(false), 2000);
              }} />
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
