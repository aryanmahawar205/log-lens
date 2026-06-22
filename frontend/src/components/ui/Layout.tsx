import { type ReactNode, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, Zap, Link as LinkIcon, Users, Search, Settings, Shield, UploadCloud } from 'lucide-react';
import { TopBar } from '../TopBar';
import { useDatasetContext } from '../../context/DatasetContext';
import { FileUpload } from '../FileUpload';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { datasets, loading } = useDatasetContext();
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Traffic', path: '/traffic', icon: Activity },
    { name: 'Performance', path: '/performance', icon: Zap },
    { name: 'URLs', path: '/urls', icon: LinkIcon },
    { name: 'Visitors', path: '/visitors', icon: Users },
    { name: 'Security', path: '/security', icon: Shield },
    { name: 'Log Explorer', path: '/explorer', icon: Search },
  ];

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-800">
          <Activity className="w-6 h-6 text-blue-500 mr-2" />
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">LogLens</span>
        </div>

        <nav className="flex-1 py-4 overflow-y-auto">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.name}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center px-3 py-2 rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-500/10 text-blue-400'
                          : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
                      }`
                    }
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button className="flex items-center text-gray-400 hover:text-gray-100 transition-colors">
            <Settings className="w-5 h-5 mr-3" />
            Settings
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 bg-gray-950">
          <div className="max-w-7xl mx-auto h-full">
            {loading ? (
              <div className="flex items-center justify-center h-full text-gray-400">
                Loading datasets...
              </div>
            ) : datasets.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <DatabaseIcon className="w-16 h-16 text-gray-700 mb-4" />
                <h2 className="text-2xl font-semibold text-gray-200 mb-2">No datasets uploaded.</h2>
                <p className="text-gray-400 mb-6 max-w-md">
                  Upload a log file to begin analyzing your traffic, performance, and security metrics.
                </p>
                <button
                  onClick={() => setIsUploadOpen(true)}
                  className="flex items-center px-6 py-3 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
                >
                  <UploadCloud className="w-5 h-5 mr-2" />
                  Upload Dataset
                </button>
              </div>
            ) : (
              children
            )}
          </div>
        </main>
      </div>

      {isUploadOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-gray-800">
              <h2 className="text-lg font-semibold text-white">Upload Log File</h2>
              <button onClick={() => setIsUploadOpen(false)} className="text-gray-400 hover:text-white">
                <XIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <FileUpload onSuccess={() => {
                setTimeout(() => setIsUploadOpen(false), 1500);
              }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Inline icons for empty state to avoid adding new imports to top if unnecessary
function DatabaseIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  );
}

function XIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
        </svg>
    )
}
