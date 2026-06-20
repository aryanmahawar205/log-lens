import { type ReactNode } from 'react';

export interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  keyExtractor: (row: T, index: number) => string | number;
  className?: string;
}

export function DataTable<T>({ data, columns, keyExtractor, className = '' }: DataTableProps<T>) {
  if (!data || data.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-500 border border-gray-800 rounded-lg bg-gray-900/50">
        No records found.
      </div>
    );
  }

  return (
    <div className={`overflow-x-auto rounded-lg border border-gray-800 bg-gray-900 ${className}`}>
      <table className="w-full text-sm text-left whitespace-nowrap">
        <thead className="text-xs text-gray-400 bg-gray-800/50 uppercase">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} scope="col" className={`px-4 py-3 font-medium ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {data.map((row, rowIndex) => (
            <tr key={keyExtractor(row, rowIndex)} className="hover:bg-gray-800/30 transition-colors">
              {columns.map((col, colIndex) => (
                <td key={colIndex} className={`px-4 py-3 text-gray-300 ${col.className || ''}`}>
                  {col.cell ? col.cell(row) : col.accessorKey ? String(row[col.accessorKey]) : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
