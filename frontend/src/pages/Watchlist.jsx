import { useState, useEffect } from 'react';
import { watchlistAPI } from '../services/api';
import StockCard from '../components/StockCard';
import SkeletonCard from '../components/SkeletonCard';
import { Eye, Info, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Watchlist() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      const res = await watchlistAPI.get();
      // The API returns { count, watchlist: [...] }
      setStocks(res.data.watchlist || []);
    } catch (err) {
      toast.error('Failed to load watchlist');
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };

  const removeFromWatchlist = async (ticker) => {
    try {
      await watchlistAPI.remove(ticker);
      setStocks(prev => prev.filter(s => s.ticker !== ticker));
      toast.success(`Removed ${ticker} from watchlist`);
    } catch (err) {
      toast.error('Failed to update watchlist');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-1">
          <Eye className="w-6 h-6 text-[var(--color-accent-blue)]" />
          My Watchlist
        </h1>
        <p className="text-[var(--color-text-secondary)] text-sm">
          Tracked companies and their latest risk analysis
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
        </div>
      ) : stocks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stocks.map(stock => (
            <StockCard 
              key={stock.ticker} 
              stock={{...stock, in_watchlist: true}} 
              onToggleWatchlist={removeFromWatchlist}
            />
          ))}
        </div>
      ) : (
        <div className="glass-card-transparent p-12 flex flex-col items-center justify-center text-center max-w-2xl mx-auto mt-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="w-20 h-20 rounded-full bg-[var(--color-bg-secondary)] flex items-center justify-center mb-6">
            <Eye className="w-10 h-10 text-[var(--color-text-muted)] opacity-50" />
          </div>
          <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-3">Your watchlist is empty</h3>
          <p className="text-[var(--color-text-secondary)] text-base max-w-md mb-8">
            Keep an eye on critical stock movements and insider dilution by adding companies from the market dashboard.
          </p>
          <a href="/" className="px-6 py-2.5 bg-[var(--color-accent-blue)] hover:bg-blue-600 text-white font-medium rounded-lg transition-colors flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Explore Dashboard
          </a>
        </div>
      )}
    </div>
  );
}
