import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { scannerAPI } from '../services/api';
import {
  LayoutDashboard, Eye, Bell, Search, LogOut, ChevronDown,
  RefreshCw, Activity, User
} from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [scanStatus, setScanStatus] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await scannerAPI.status();
        setScanStatus(res.data);
      } catch (e) { /* ignore */ }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/watchlist', label: 'Watchlist', icon: Eye },
    { path: '/alerts', label: 'Alerts', icon: Bell },
  ];

  return (
    <nav className="sticky top-0 z-50 glass-card border-b border-[var(--color-border)] px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <Activity className="w-6 h-6 text-[var(--color-accent-blue)]" />
          <span className="text-lg font-bold text-gradient hidden sm:inline">PromoterAI</span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${location.pathname === path
                  ? 'bg-[var(--color-accent-blue)]/15 text-[var(--color-accent-blue)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/5'
                }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden md:inline">{label}</span>
            </Link>
          ))}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="hidden md:flex items-center flex-1 max-w-xs">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-9 pr-3 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent-blue)]/50 transition"
            />
          </div>
        </form>

        {/* Scan Status */}
        {scanStatus?.status === 'running' && (
          <div className="flex items-center gap-2 text-xs text-[var(--color-accent-amber)]">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span className="hidden sm:inline">
              Scanning {scanStatus.current_ticker}... ({scanStatus.progress}/{scanStatus.total})
            </span>
          </div>
        )}

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition text-sm"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--color-accent-blue)] to-[var(--color-accent-purple)] flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="hidden sm:inline text-[var(--color-text-secondary)]">
              {user?.display_name || user?.username}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
          </button>

          {showUserMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
              <div className="absolute right-0 mt-2 w-48 glass-card border border-[var(--color-border)] rounded-lg py-1 z-50">
                <div className="px-4 py-2 border-b border-[var(--color-border)]">
                  <p className="text-sm font-medium">{user?.display_name || user?.username}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">@{user?.username}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[var(--color-accent-red)] hover:bg-white/5 transition"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
