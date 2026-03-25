import { useState, useEffect } from 'react';
import { watchlistAPI } from '../services/api';
import StockCard from '../components/StockCard';
import { Eye, Info } from 'lucide-react';
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
      setStocks(res.data);
    } catch (err) {
      toast.error('Failed to load watchlist');
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
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-[var(--color-accent-blue)] border-t-transparent rounded-full animate-spin" />
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
        <div className="glass-card p-12 text-center max-w-md mx-auto">
          <Info className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Your watchlist is empty</h3>
          <p className="text-[var(--color-text-secondary)] text-sm mb-6">
            Keep an eye on critical stock movements by adding companies from the dashboard.
          </p>
        </div>
      )}
    </div>
  );
}
