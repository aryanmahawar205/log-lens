import { useState, useEffect } from 'react';
import { Folder, CheckCircle, AlertCircle, Loader2, Save } from 'lucide-react';
import { useDatasetContext } from '../context/DatasetContext';
import { API_BASE, SYSTEM_API_BASE } from "../config/api";

interface FolderImportProps {
  onSuccess?: () => void;
}

export function FolderImport({ onSuccess }: FolderImportProps) {
  const [folderPath, setFolderPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);

  const { refreshDatasets } = useDatasetContext();

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch(`${SYSTEM_API_BASE}/settings`);
        if (response.ok) {
          const data = await response.json();
          if (data.enterprise_log_directory) {
            setFolderPath(data.enterprise_log_directory);
          }
        }
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoadingSettings(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSaveSettings = async () => {
    try {
      const response = await fetch(`${SYSTEM_API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enterprise_log_directory: folderPath }),
      });
      if (!response.ok) {
        throw new Error("Failed to save default path");
      }
      alert("Default path saved successfully.");
    } catch (err) {
      console.error(err);
      alert("Failed to save default path.");
    }
  };

  const handleImport = async () => {
    if (!folderPath) return;

    setScanning(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/upload/folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Import failed');
      }

      setResult(data);
      await refreshDatasets(false);
      if (onSuccess) onSuccess();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setScanning(false);
    }
  };

  if (loadingSettings) {
    return (
      <div className="flex justify-center items-center py-8">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full">
      {!result && !scanning && (
        <div className="space-y-4">
          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <h3 className="text-white font-medium mb-4 flex items-center">
              <Folder className="w-5 h-5 mr-2 text-blue-400" />
              Enterprise Folder Ingestion
            </h3>

            <p className="text-gray-400 text-sm mb-4">
              Recursively scan a directory for log files. Supported formats will be automatically imported. Existing files will be skipped (incremental scan).
            </p>

            <div className="space-y-2">
              <label className="text-sm text-gray-400 font-medium">Directory Path</label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  placeholder="/var/log/apache2/ or D:\\Logs"
                  className="flex-1 bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleSaveSettings}
                  title="Save as Default"
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
                >
                  <Save className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleImport}
              disabled={!folderPath}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white rounded-md font-medium transition-colors"
            >
              Start Folder Scan
            </button>
          </div>
        </div>
      )}

      {scanning && (
        <div className="border border-gray-700 bg-gray-800/50 rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[200px]">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
          <h3 className="text-white font-medium mb-2">Scanning Directory...</h3>
          <p className="text-gray-400 text-sm">This may take a while depending on the number of files and their size.</p>
        </div>
      )}

      {result && (
        <div className="border border-emerald-900/50 bg-emerald-950/20 rounded-xl p-6">
          <div className="flex items-center text-emerald-400 mb-4 border-b border-emerald-900/50 pb-4">
            <CheckCircle className="w-6 h-6 mr-2" />
            <h3 className="text-lg font-medium">Scan Completed</h3>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Files Discovered</span>
              <span className="text-white font-medium">{result.details.files_discovered}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">New Files Imported</span>
              <span className="text-emerald-400 font-bold">{result.details.files_imported}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Files Skipped (Duplicates/Errors)</span>
              <span className="text-yellow-400 font-medium">{result.details.files_skipped}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Unsupported Files</span>
              <span className="text-gray-500 font-medium">{result.details.files_unsupported}</span>
            </div>
            <div className="flex justify-between items-center mt-2 pt-2 border-t border-emerald-900/50">
              <span className="text-gray-400">Duration</span>
              <span className="text-white font-medium">{result.details.duration_sec.toFixed(2)}s</span>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={() => setResult(null)}
              className="px-6 py-2 border border-gray-700 hover:bg-gray-800 text-white rounded-md font-medium transition-colors"
            >
              Scan Another Folder
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 border border-rose-900/50 bg-rose-950/20 rounded-lg flex items-start text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 mr-2 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}
    </div>
  );
}
