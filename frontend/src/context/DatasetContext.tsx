import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

export interface Dataset {
  id: number;
  filename: string;
  format: string;
  uploaded_at: string;
  total_entries: number;
  parser_used: string;
  confidence: number;
}

interface DatasetContextType {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  refreshDatasets: (autoSelectLatest?: boolean) => Promise<void>;
  selectDataset: (id: number) => void;
  deleteDataset: (id: number) => Promise<void>;
  loading: boolean;
}

const DatasetContext = createContext<DatasetContextType | undefined>(undefined);

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  `${window.location.origin.replace('-3000.app.github.dev', '-8000.app.github.dev')}/api/v1/analytics`;

const DATASET_STORAGE_KEY = 'loglens_dataset_id';

export function DatasetProvider({ children }: { children: ReactNode }) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDatasets = async () => {
    try {
      // Determine API URL based on environment/location to avoid hardcoding localhost
      const apiUrl = window.location.hostname === 'localhost'
        ? 'http://localhost:8000/api/v1/analytics/datasets'
        : `${API_BASE_URL}/datasets`;

      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch datasets');
      }
      return await response.json();
    } catch (err) {
      console.error("Failed to fetch datasets", err);
      return [];
    }
  };

  const refreshDatasets = useCallback(async (autoSelectLatest = false) => {
    setLoading(true);
    const data = await fetchDatasets();
    setDatasets(data);

    if (data.length > 0) {
      let nextId = data[0].id; // default to most recent (assuming API returns sorted by uploaded_at DESC)

      if (!autoSelectLatest) {
        const storedId = localStorage.getItem(DATASET_STORAGE_KEY);
        if (storedId) {
          const parsedId = parseInt(storedId, 10);
          const exists = data.some((d: Dataset) => d.id === parsedId);
          if (exists) {
            nextId = parsedId;
          }
        }
      }

      setSelectedDatasetId(nextId);
      localStorage.setItem(DATASET_STORAGE_KEY, nextId.toString());
    } else {
      setSelectedDatasetId(null);
      localStorage.removeItem(DATASET_STORAGE_KEY);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  const selectDataset = useCallback((id: number) => {
    setSelectedDatasetId(id);
    localStorage.setItem(DATASET_STORAGE_KEY, id.toString());
  }, []);

  const deleteDataset = useCallback(async (id: number) => {
    try {
      const apiUrl = window.location.hostname === 'localhost'
        ? `http://localhost:8000/api/v1/analytics/datasets/${id}`
        : `${API_BASE_URL}/datasets/${id}`;

      const response = await fetch(apiUrl, { method: 'DELETE' });
      if (!response.ok) {
        throw new Error('Failed to delete dataset');
      }
      // when deleting, we just refresh and don't auto select latest necessarily unless current was deleted
      // Wait, we can just do normal refreshDatasets() because if current is deleted, it won't exist in new data and it will fallback to latest.
      await refreshDatasets(false);
    } catch (err) {
      console.error("Failed to delete dataset", err);
    }
  }, [refreshDatasets]);

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId) || null;

  // Defensive handling: If selectedDataset is null but datasets exist, it means selection is invalid.
  // The refresh logic handles this on load, but if datasets are updated externally, it ensures sync.
  useEffect(() => {
    if (datasets.length > 0 && selectedDatasetId !== null && !selectedDataset) {
      // selectedDatasetId exists but is not in datasets (e.g. 404 from backend later)
      const nextId = datasets[0].id;
      setSelectedDatasetId(nextId);
      localStorage.setItem(DATASET_STORAGE_KEY, nextId.toString());
    } else if (datasets.length === 0 && selectedDatasetId !== null) {
      setSelectedDatasetId(null);
      localStorage.removeItem(DATASET_STORAGE_KEY);
    }
  }, [datasets, selectedDatasetId, selectedDataset]);

  return (
    <DatasetContext.Provider value={{ datasets, selectedDataset, refreshDatasets, selectDataset, deleteDataset, loading }}>
      {children}
    </DatasetContext.Provider>
  );
}

export function useDatasetContext() {
  const context = useContext(DatasetContext);
  if (context === undefined) {
    throw new Error('useDatasetContext must be used within a DatasetProvider');
  }
  return context;
}
