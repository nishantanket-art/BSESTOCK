import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { stocksAPI, watchlistAPI, scannerAPI } from '../services/api';
import StockCard from '../components/StockCard';
import SkeletonCard from '../components/SkeletonCard';
import { Filter, Search, TrendingUp, TrendingDown, AlertTriangle, Info, Play, Activity, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const POLL_INTERVAL_MS = 60_000; // Auto-refresh every 60 seconds
const MAX_RETRIES = 3;

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [watchlist, setWatchlist] = useState(new Set());
  
  const [lastUpdated, setLastUpdated] = useState(null);
  const pollTimerRef = useRef(null);
  const retryCountRef = useRef(0);

  const [filters, setFilters] = useState({
    riskLevel: searchParams.get('risk_level') || '',
    verdict: searchParams.get('verdict') || '',
    search: searchParams.get('search') || '',
  });

  const fetchData = useCallback(async (isPolling = false) => {
    if (!isPolling) setLoading(true);
    try {
      const params = { limit: 200 };
      if (filters.riskLevel) {
        params.risk = filters.riskLevel;
        params.risk_level = filters.riskLevel; // Send both for compat
      }
      if (filters.verdict) params.verdict = filters.verdict;
      if (filters.search) params.search = filters.search;
      
      const [stocksRes, watchlistRes] = await Promise.all([
        stocksAPI.list(params),
        watchlistAPI.get().catch(() => ({ data: [] }))
      ]);
      
      const results = stocksRes.data.results || [];
      console.log(`[StoXeye] Fetched ${results.length} stocks`, { count: stocksRes.data.count });
      setStocks(results);
      const wlData = Array.isArray(watchlistRes.data) ? watchlistRes.data : [];
      setWatchlist(new Set(wlData.map(item => item.ticker)));
      setLastUpdated(new Date());
      retryCountRef.current = 0; // Reset retries on success
    } catch (err) {
      console.error("[StoXeye] API Fetch Error:", {
        message: err.message,
        url: err.config?.url,
        status: err.response?.status,
        data: err.response?.data
      });
      // Retry with exponential backoff
      if (retryCountRef.current < MAX_RETRIES) {
        retryCountRef.current++;
        const delay = Math.pow(2, retryCountRef.current) * 1000;
        console.log(`[StoXeye] Retrying in ${delay}ms (attempt ${retryCountRef.current}/${MAX_RETRIES})`);
        setTimeout(() => fetchData(isPolling), delay);
        return;
      }
      if (!isPolling) toast.error('Failed to connect to API server');
    } finally {
      if (!isPolling) setLoading(false);
    }
  }, [filters]);

  // Initial fetch + filter changes
  useEffect(() => {
    retryCountRef.current = 0;
    fetchData();
  }, [fetchData]);

  // Auto-polling interval
  useEffect(() => {
    pollTimerRef.current = setInterval(() => {
      fetchData(true);
    }, POLL_INTERVAL_MS);
    return () => clearInterval(pollTimerRef.current);
  }, [fetchData]);

  useEffect(() => {
    const search = searchParams.get('search') || '';
    if (search !== filters.search) {
      setFilters(prev => ({ ...prev, search }));
    }
  }, [searchParams]);

  const handleRunScan = async () => {
    try {
      await scannerAPI.run();
      toast.success('Scanner started! Check the top navigation bar for progress.');
    } catch (err) {
      toast.error('Failed to start scanner');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    if (key === 'search') {
      if (value) searchParams.set('search', value);
      else searchParams.delete('search');
      setSearchParams(searchParams);
    }
  };

  const toggleWatchlist = async (ticker, inWatchlist) => {
    try {
      if (inWatchlist) {
        await watchlistAPI.remove(ticker);
        setWatchlist(prev => {
          const next = new Set(prev);
          next.delete(ticker);
          return next;
        });
        toast.success(`Removed ${ticker} from watchlist`);
      } else {
        await watchlistAPI.add(ticker);
        setWatchlist(prev => new Set(prev).add(ticker));
        toast.success(`Added ${ticker} to watchlist`);
      }
    } catch (err) {
      toast.error('Failed to update watchlist');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-1">Market Dashboard</h1>
          <p className="text-[var(--color-text-secondary)] text-sm flex items-center gap-2">
            Monitor promoter stake changes across Indian stocks
            {lastUpdated && (
              <span className="text-[var(--color-text-muted)] text-xs">
                · Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <button 
            onClick={handleRunScan}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--color-accent-blue)] hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition"
          >
            <Play className="w-3.5 h-3.5" />
            Run Scan
          </button>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Filter by ticker..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-9 pr-3 py-1.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)]"
            />
          </div>
          
          <select
            value={filters.riskLevel}
            onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
            className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)]"
          >
            <option value="">All Risks</option>
            <option value="High">🔴 High Risk</option>
            <option value="Medium">🟠 Medium Risk</option>
            <option value="Low">🟢 Low Risk</option>
          </select>

          <select
            value={filters.verdict}
            onChange={(e) => handleFilterChange('verdict', e.target.value)}
            className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)]"
          >
            <option value="">All Verdicts</option>
            <option value="Exit">⚠️ Exit</option>
            <option value="Caution">👀 Caution</option>
            <option value="Hold">⏸️ Hold</option>
            <option value="Buy">✅ Buy</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : stocks.length > 0 ? (
        <>
          {/* Top Movers Section */}
          {!filters.search && !filters.riskLevel && !filters.verdict && stocks.length >= 4 && (
            <div className="mb-8 hidden sm:block">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-[var(--color-accent-blue)]" />
                Market Highlights
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass-card-transparent p-4 flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-[var(--color-accent-emerald)] font-medium text-sm">
                    <TrendingUp className="w-4 h-4" /> Top Accumulation
                  </div>
                  <div className="space-y-2">
                    {stocks.filter(s => Number(s.promoter_change) > 0).sort((a,b) => Number(b.promoter_change) - Number(a.promoter_change)).slice(0, 2).map(s => (
                       <StockCard key={s.ticker} stock={{...s, in_watchlist: watchlist.has(s.ticker)}} onToggleWatchlist={toggleWatchlist} />
                    ))}
                  </div>
                </div>
                <div className="glass-card-transparent p-4 flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-[var(--color-accent-red)] font-medium text-sm">
                    <TrendingDown className="w-4 h-4" /> Top Dilution
                  </div>
                  <div className="space-y-2">
                    {stocks.filter(s => Number(s.promoter_change) < 0).sort((a,b) => Number(a.promoter_change) - Number(b.promoter_change)).slice(0, 2).map(s => (
                       <StockCard key={s.ticker} stock={{...s, in_watchlist: watchlist.has(s.ticker)}} onToggleWatchlist={toggleWatchlist} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">All Monitored Stocks</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {stocks.filter(s => s && s.ticker).map(stock => (
              <StockCard 
                key={stock.ticker} 
                stock={{...stock, in_watchlist: watchlist.has(stock.ticker)}} 
                onToggleWatchlist={toggleWatchlist}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="glass-card p-8 text-center bg-[var(--color-bg-card)]">
          <Info className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4" />
          <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">No stocks found</h3>
          <p className="text-[var(--color-text-secondary)] text-sm">
            Try adjusting your filters or running a new scan.
          </p>
        </div>
      )}
    </div>
  );
}
