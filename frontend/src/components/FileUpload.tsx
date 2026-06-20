import { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onSuccess?: () => void;
}

export function FileUpload({ onSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/analytics/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setResult(data);
      if (onSuccess) onSuccess();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full">
      {!result && !uploading && (
        <div
          className="border-2 border-dashed border-gray-700 hover:border-blue-500 bg-gray-800/50 rounded-xl p-8 text-center transition-colors cursor-pointer"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".log,.txt,.gz,.bz2"
          />
          <UploadCloud className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          {file ? (
            <div>
              <p className="text-white font-medium mb-1">{file.name}</p>
              <p className="text-gray-400 text-sm">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
          ) : (
            <div>
              <p className="text-white font-medium mb-1">Click or drag log file to upload</p>
              <p className="text-gray-500 text-sm">Supports raw text logs, .gz, and .bz2</p>
            </div>
          )}
        </div>
      )}

      {uploading && (
        <div className="border border-gray-700 bg-gray-800/50 rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[200px]">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
          <h3 className="text-white font-medium mb-2">Ingesting Logs...</h3>
          <p className="text-gray-400 text-sm">This might take a moment depending on the file size.</p>
        </div>
      )}

      {result && (
        <div className="border border-emerald-900/50 bg-emerald-950/20 rounded-xl p-6">
          <div className="flex items-center text-emerald-400 mb-4 border-b border-emerald-900/50 pb-4">
            <CheckCircle className="w-6 h-6 mr-2" />
            <h3 className="text-lg font-medium">Upload Successful</h3>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Detected Format</span>
              <span className="text-white font-medium bg-gray-800 px-2 py-1 rounded text-sm">{result.format}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Confidence Score</span>
              <span className="text-white font-medium">{Math.round(result.confidence * 100)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Records Processed</span>
              <span className="text-emerald-400 font-bold">{result.message.replace(/[^0-9]/g, '')} entries</span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 border border-rose-900/50 bg-rose-950/20 rounded-lg flex items-start text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 mr-2 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {!uploading && !result && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={!file}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white rounded-md font-medium transition-colors"
          >
            Start Analysis
          </button>
        </div>
      )}

      {result && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => { setFile(null); setResult(null); }}
            className="px-6 py-2 border border-gray-700 hover:bg-gray-800 text-white rounded-md font-medium transition-colors"
          >
            Upload Another
          </button>
        </div>
      )}
    </div>
  );
}
