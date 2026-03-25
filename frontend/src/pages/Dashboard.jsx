import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { stocksAPI, watchlistAPI } from '../services/api';
import StockCard from '../components/StockCard';
import { Filter, Search, TrendingUp, AlertTriangle, Info } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [watchlist, setWatchlist] = useState(new Set());
  
  const [filters, setFilters] = useState({
    riskLevel: searchParams.get('risk_level') || '',
    verdict: searchParams.get('verdict') || '',
    search: searchParams.get('search') || '',
  });

  useEffect(() => {
    fetchData();
  }, [filters]);

  useEffect(() => {
    const search = searchParams.get('search') || '';
    if (search !== filters.search) {
      setFilters(prev => ({ ...prev, search }));
    }
  }, [searchParams]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.riskLevel) params.risk_level = filters.riskLevel;
      if (filters.verdict) params.verdict = filters.verdict;
      if (filters.search) params.search = filters.search;
      
      const [stocksRes, watchlistRes] = await Promise.all([
        stocksAPI.list(params),
        watchlistAPI.get()
      ]);
      
      setStocks(stocksRes.data);
      setWatchlist(new Set(watchlistRes.data.map(item => item.ticker)));
    } catch (err) {
      console.error(err);
      toast.error('Failed to load stocks data');
    } finally {
      setLoading(false);
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
          <p className="text-[var(--color-text-secondary)] text-sm">Monitor promoter stake changes across Indian stocks</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
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
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-[var(--color-accent-blue)] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : stocks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stocks.map(stock => (
            <StockCard 
              key={stock.ticker} 
              stock={{...stock, in_watchlist: watchlist.has(stock.ticker)}} 
              onToggleWatchlist={toggleWatchlist}
            />
          ))}
        </div>
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
