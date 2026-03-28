import { Link } from 'react-router-dom';
import { TrendingDown, TrendingUp, Eye, EyeOff } from 'lucide-react';

export default function StockCard({ stock, onToggleWatchlist, index = 0 }) {
  const riskClass = {
    High: 'bg-red-500/10 text-red-500 border-red-500/20 shadow-[0_0_15px_-5px_rgba(239,68,68,0.3)]',
    Medium: 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-[0_0_15px_-5px_rgba(245,158,11,0.3)]',
    Low: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-[0_0_15px_-5px_rgba(16,185,129,0.3)]',
  }[stock.risk_level] || 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';

  const verdictColor = {
    Exit: 'text-[var(--color-accent-red)]',
    Caution: 'text-[var(--color-accent-amber)]',
    Hold: 'text-[var(--color-text-secondary)]',
    Buy: 'text-[var(--color-accent-emerald)]',
  }[stock.verdict] || 'text-[var(--color-text-secondary)]';

  const formatNum = (v, dec=1) => {
    if (v === null || v === undefined || isNaN(Number(v))) return '—';
    return Number(v).toFixed(dec);
  };

  return (
    <div className="glass-card p-5 group relative overflow-hidden flex flex-col h-full rounded-2xl">
      {/* Dynamic Background Glow */}
      <div className={`absolute -top-12 -right-12 w-32 h-32 blur-[60px] opacity-0 group-hover:opacity-20 transition-opacity duration-500
        ${stock.verdict === 'Buy' ? 'bg-emerald-500' : stock.verdict === 'Exit' ? 'bg-red-500' : 'bg-blue-500'}`} 
      />

      <div className="relative z-10 flex-1">
        <div className="flex items-start justify-between mb-4">
          <div className="min-w-0 flex-1">
            <Link to={`/company/${stock.ticker}`} className="inline-block">
              <h3 className="text-xl font-extrabold text-white tracking-tight group-hover:text-[var(--color-accent-blue)] transition-colors duration-300">
                {stock.ticker}
              </h3>
            </Link>
            <p className="text-xs text-[var(--color-text-muted)] font-medium truncate mt-0.5">
              {stock.company_name}
            </p>
          </div>
          <span className={`text-[9px] px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider ${riskClass}`}>
            {stock.risk_level} Risk
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-5">
          <div className="bg-white/5 border border-white/5 rounded-xl p-3">
            <p className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-widest mb-1">STAKE</p>
            <p className="text-lg font-bold text-white leading-none">{formatNum(stock.promoter_current)}%</p>
          </div>
          <div className="bg-white/5 border border-white/5 rounded-xl p-3">
            <p className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-widest mb-1">CHG</p>
            <div className="flex items-center gap-1">
              <span className={`text-lg font-bold leading-none ${Number(stock.promoter_change) > 0 ? 'text-[var(--color-accent-emerald)]' : Number(stock.promoter_change) < 0 ? 'text-[var(--color-accent-red)]' : 'text-zinc-400'}`}>
                {Number(stock.promoter_change) > 0 ? '+' : ''}{formatNum(stock.promoter_change, 2)}%
              </span>
            </div>
          </div>
        </div>

        {stock.current_price && (
          <div className="mb-4">
             <p className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-widest mb-1">CURRENT PRICE</p>
             <p className="text-lg font-extrabold text-white">₹{stock.current_price.toLocaleString('en-IN')}</p>
          </div>
        )}
      </div>

      <div className="relative z-10 pt-4 border-t border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${stock.verdict === 'Buy' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-zinc-600'}`} />
          <span className={`text-xs font-black uppercase tracking-widest ${verdictColor}`}>
            {stock.verdict}
          </span>
        </div>
        
        {onToggleWatchlist && (
          <button
            onClick={(e) => { e.preventDefault(); onToggleWatchlist(stock.ticker, stock.in_watchlist); }}
            className={`p-2 rounded-xl border transition-all duration-300 ${stock.in_watchlist ? 'bg-[var(--color-accent-blue)] border-[var(--color-accent-blue)] text-white shadow-lg shadow-blue-500/30' : 'bg-white/5 border-white/5 text-[var(--color-text-muted)] hover:text-white hover:border-white/20'}`}
          >
            {stock.in_watchlist ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}
