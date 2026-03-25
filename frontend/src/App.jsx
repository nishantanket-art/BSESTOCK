import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

import Navbar from './components/Navbar';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import CompanyDetail from './pages/CompanyDetail';
import Watchlist from './pages/Watchlist';
import Alerts from './pages/Alerts';

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// Layout wrapper for authenticated pages
function AppLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 overflow-x-hidden pt-4 pb-12">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster 
          position="bottom-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'var(--color-bg-card)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
            },
            success: {
              iconTheme: { primary: 'var(--color-accent-emerald)', secondary: 'var(--color-bg-card)' }
            },
            error: {
              iconTheme: { primary: 'var(--color-accent-red)', secondary: 'var(--color-bg-card)' }
            }
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          <Route path="/" element={
            <PrivateRoute>
              <AppLayout><Dashboard /></AppLayout>
            </PrivateRoute>
          } />
          
          <Route path="/company/:ticker" element={
            <PrivateRoute>
              <AppLayout><CompanyDetail /></AppLayout>
            </PrivateRoute>
          } />
          
          <Route path="/watchlist" element={
            <PrivateRoute>
              <AppLayout><Watchlist /></AppLayout>
            </PrivateRoute>
          } />
          
          <Route path="/alerts" element={
            <PrivateRoute>
              <AppLayout><Alerts /></AppLayout>
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
