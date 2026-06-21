import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/ui/Layout';
import { Dashboard } from './pages/Dashboard';
import { TrafficAnalytics } from './pages/TrafficAnalytics';
import { PerformanceAnalytics } from './pages/PerformanceAnalytics';
import { UrlAnalytics } from './pages/UrlAnalytics';
import { VisitorAnalytics } from './pages/VisitorAnalytics';
import { LogExplorer } from './pages/LogExplorer';
import { SecurityAnalytics } from './pages/SecurityAnalytics';
import { FilterProvider } from './context/FilterContext';

function App() {
  return (
    <FilterProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/traffic" element={<TrafficAnalytics />} />
            <Route path="/performance" element={<PerformanceAnalytics />} />
            <Route path="/urls" element={<UrlAnalytics />} />
            <Route path="/visitors" element={<VisitorAnalytics />} />
            <Route path="/security" element={<SecurityAnalytics />} />
            <Route path="/explorer" element={<LogExplorer />} />
          </Routes>
        </Layout>
      </Router>
    </FilterProvider>
  );
}

export default App;
