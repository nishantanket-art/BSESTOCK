import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { scannerAPI } from '../services/api';
import {
  LayoutDashboard, Eye, Bell, Search, LogOut, ChevronDown,
  RefreshCw, Activity, User, X
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [scanStatus, setScanStatus] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [allStocks, setAllStocks] = useState([]);

  useEffect(() => {
    // Fetch all stocks for client-side autocomplete
    const fetchStocks = async () => {
      try {
        const res = await stocksAPI.list();
        setAllStocks(res.data.results || []);
      } catch (e) { /* silent fail */ }
    };
    fetchStocks();
    
    let wasRunning = false;
    const interval = setInterval(async () => {
      try {
        const res = await scannerAPI.status();
        setScanStatus(res.data);
        if (res.data.status === 'running') {
          wasRunning = true;
        } else if (res.data.status === 'done' && wasRunning) {
          wasRunning = false;
          window.location.reload();
        }
      } catch (e) { /* ignore */ }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?search=${encodeURIComponent(searchQuery.trim())}`);
      setIsSearchFocused(false);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (query.trim()) {
      const results = allStocks.filter(s => 
        s.ticker.toLowerCase().includes(query.toLowerCase()) || 
        (s.company_name && s.company_name.toLowerCase().includes(query.toLowerCase()))
      ).slice(0, 5);
      setSearchResults(results);
    } else {
      setSearchResults([]);
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
        <Link to="/" className="flex items-center gap-2 shrink-0 group">
          <div className="relative w-8 h-8 flex items-center justify-center bg-white/5 rounded-xl border border-white/10 group-hover:border-[var(--color-accent-blue)]/50 transition-all duration-300">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="group-hover:scale-110 transition-transform duration-300">
              <path d="M2 12C2 12 5 5 12 5C19 5 22 12 22 12C22 12 19 19 12 19C5 19 2 12 2 12Z" stroke="url(#eye-gradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="12" cy="12" r="3" stroke="url(#eye-gradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <defs>
                <linearGradient id="eye-gradient" x1="2" y1="5" x2="22" y2="19" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#2962ff" />
                  <stop offset="1" stopColor="#7c4dff" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span className="text-xl font-extrabold tracking-tighter hidden sm:inline bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            sto<span className="text-[var(--color-accent-blue)]">X</span>eye
          </span>
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
        <div className="hidden md:flex items-center flex-1 max-w-sm relative z-50">
          <form onSubmit={handleSearch} className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search stocks by ticker or name..."
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
              className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-full pl-10 pr-4 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent-blue)] focus:ring-1 focus:ring-[var(--color-accent-blue)] transition-all"
            />
            {searchQuery && (
              <button type="button" onClick={() => {setSearchQuery(''); setSearchResults([]);}} className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <X className="w-3.5 h-3.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]" />
              </button>
            )}
          </form>

          {/* Autocomplete Dropdown */}
          {isSearchFocused && searchQuery.trim() && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl shadow-2xl overflow-hidden glass-card">
              {searchResults.map(stock => (
                <div 
                  key={stock.ticker}
                  onClick={() => {
                    navigate(`/company/${stock.ticker}`);
                    setSearchQuery('');
                    setIsSearchFocused(false);
                  }}
                  className="flex items-center justify-between px-4 py-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-0"
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-[var(--color-text-primary)]">{stock.ticker}</span>
                    <span className="text-xs text-[var(--color-text-muted)]">{stock.company_name}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-medium ${stock.verdict === 'Buy' ? 'text-[var(--color-accent-emerald)] bg-emerald-500/10' : stock.verdict === 'Exit' ? 'text-[var(--color-accent-red)] bg-red-500/10' : 'text-[var(--color-text-secondary)] bg-white/5'}`}>
                    {stock.verdict}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Run Scan Button */}
        {scanStatus?.status !== 'running' && (
          <button
            onClick={async () => {
              try {
                await scannerAPI.run();
                toast.success('Scan started');
              } catch (e) {
                toast.error('Failed to start scan');
              }
            }}
            className="hidden lg:flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[var(--color-accent-blue)]/10 text-[var(--color-accent-blue)] hover:bg-[var(--color-accent-blue)]/20 transition text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Run Scan
          </button>
        )}

        {/* Scan Status */}
        {scanStatus?.status === 'running' && (
          <div className="flex items-center gap-2 text-xs text-[var(--color-accent-amber)] bg-amber-500/10 px-3 py-2 rounded-lg border border-amber-500/20">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span className="hidden sm:inline font-medium">
              Scanning {scanStatus.current_ticker}... ({scanStatus.progress}/{scanStatus.total})
            </span>
          </div>
        )}

        {/* User Info (Demo Mode) */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--color-accent-blue)] to-[var(--color-accent-purple)] flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-[var(--color-text-primary)] font-medium leading-none mb-0.5">Guest User</span>
            <span className="text-[var(--color-text-muted)] text-[10px] uppercase tracking-wider">Demo Mode</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
