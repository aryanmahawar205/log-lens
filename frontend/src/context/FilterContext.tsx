import { createContext, useContext, useState, type ReactNode, useCallback } from 'react';

export interface FilterState {
  start_date?: string;
  end_date?: string;
  ip?: string;
  url?: string;
  normalized_url?: string;
  status_code?: number;
  user_agent?: string;
  bot_classification?: string;
  [key: string]: string | number | undefined; // For future extensibility
}

interface FilterContextType {
  filters: FilterState;
  setFilter: (key: keyof FilterState, value: string | number | undefined) => void;
  setFilters: (newFilters: FilterState) => void;
  clearFilters: () => void;
  hasActiveFilters: () => boolean;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFiltersState] = useState<FilterState>({});

  const setFilter = useCallback((key: keyof FilterState, value: string | number | undefined) => {
    setFiltersState(prev => {
      const newFilters = { ...prev };
      if (value === undefined || value === '') {
        delete newFilters[key];
      } else {
        newFilters[key] = value;
      }
      return newFilters;
    });
  }, []);

  const setFilters = useCallback((newFilters: FilterState) => {
    setFiltersState(newFilters);
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState({});
  }, []);

  const hasActiveFilters = useCallback(() => {
    return Object.keys(filters).length > 0;
  }, [filters]);

  return (
    <FilterContext.Provider value={{ filters, setFilter, setFilters, clearFilters, hasActiveFilters }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilterContext() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilterContext must be used within a FilterProvider');
  }
  return context;
}
