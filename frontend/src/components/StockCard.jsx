import { Link } from 'react-router-dom';
import { TrendingDown, TrendingUp, Eye, EyeOff } from 'lucide-react';

export default function StockCard({ stock, onToggleWatchlist }) {
  const riskClass = {
    High: 'risk-badge-high',
    Medium: 'risk-badge-medium',
    Low: 'risk-badge-low',
  }[stock.risk_level] || 'risk-badge-low';

  const verdictColors = {
    Exit: 'text-[var(--color-verdict-exit)]',
    Caution: 'text-[var(--color-verdict-caution)]',
    Hold: 'text-[var(--color-verdict-hold)]',
    Buy: 'text-[var(--color-verdict-buy)]',
  };

  return (
    <div className="glass-card p-4 hover:bg-[var(--color-bg-card-hover)] hover:-translate-y-1 hover:shadow-xl hover:border-[var(--color-border-light)] transition-all duration-300 group relative overflow-hidden">
      {/* Accent left border on hover */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300
        ${stock.verdict === 'Exit' || stock.verdict === 'Caution' ? 'bg-[var(--color-accent-red)]' : 
          stock.verdict === 'Buy' ? 'bg-[var(--color-accent-emerald)]' : 'bg-[var(--color-accent-blue)]'}`} 
      />

      <div className="flex items-start justify-between gap-3 relative z-10 pl-1">
        {/* Left: Company Info */}
        <Link to={`/company/${stock.ticker}`} className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-base font-bold text-[var(--color-text-primary)] group-hover:text-[var(--color-accent-blue)] transition truncate">
              {stock.ticker}
            </h3>
            <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-wide ${riskClass}`}>
              {stock.risk_level}
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] truncate mb-4 font-medium">
            {stock.company_name}
          </p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
            <div className="flex flex-col">
              <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-0.5">Promoter</span>
              <span className="text-[var(--color-text-primary)] font-semibold">{stock.promoter_current?.toFixed(1)}%</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-0.5">Change</span>
              <div className="flex items-center gap-1">
                {stock.promoter_change < 0 ? (
                  <TrendingDown className="w-3 h-3 text-[var(--color-accent-red)]" />
                ) : stock.promoter_change > 0 ? (
                  <TrendingUp className="w-3 h-3 text-[var(--color-accent-emerald)]" />
                ) : null}
                <span className={`font-semibold ${stock.promoter_change < 0 ? 'text-[var(--color-accent-red)]' : stock.promoter_change > 0 ? 'text-[var(--color-accent-emerald)]' : 'text-[var(--color-text-secondary)]'}`}>
                  {stock.promoter_change !== undefined ? `${stock.promoter_change > 0 ? '+' : ''}${stock.promoter_change.toFixed(2)}%` : '0.00%'}
                </span>
              </div>
            </div>
            {stock.market_cap && stock.market_cap !== 'N/A' && (
              <div className="flex flex-col hidden sm:flex">
                <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-0.5">M.Cap</span>
                <span className="text-[var(--color-text-secondary)] font-medium">{stock.market_cap}</span>
              </div>
            )}
          </div>
        </Link>

        {/* Right: Verdict + Watchlist */}
        <div className="flex flex-col items-end gap-3 shrink-0">
          <span className={`text-xs font-bold px-2.5 py-1 rounded bg-white/5 border border-white/5 ${verdictColors[stock.verdict] || 'text-[var(--color-text-secondary)]'}`}>
            {stock.verdict_icon} {stock.verdict}
          </span>
          {onToggleWatchlist && (
            <button
              onClick={(e) => { e.preventDefault(); onToggleWatchlist(stock.ticker, stock.in_watchlist); }}
              className={`p-1.5 rounded-md transition ${stock.in_watchlist ? 'bg-[var(--color-accent-blue)]/10 text-[var(--color-accent-blue)]' : 'hover:bg-white/10 text-[var(--color-text-muted)]'}`}
              title={stock.in_watchlist ? 'Remove from watchlist' : 'Add to watchlist'}
            >
              {stock.in_watchlist ? (
                <Eye className="w-4 h-4" />
              ) : (
                <EyeOff className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
