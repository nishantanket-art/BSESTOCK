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
    <div className="glass-card p-4 hover:bg-[var(--color-bg-card-hover)] transition-all duration-300 group">
      <div className="flex items-start justify-between gap-3">
        {/* Left: Company Info */}
        <Link to={`/company/${stock.ticker}`} className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-accent-blue)] transition truncate">
              {stock.ticker}
            </h3>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskClass}`}>
              {stock.risk_level}
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] truncate mb-2">
            {stock.company_name}
          </p>
          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-[var(--color-text-muted)]">Holding: </span>
              <span className="text-[var(--color-text-primary)] font-medium">{stock.promoter_current?.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-1">
              {stock.promoter_change < 0 ? (
                <TrendingDown className="w-3 h-3 text-[var(--color-accent-red)]" />
              ) : (
                <TrendingUp className="w-3 h-3 text-[var(--color-accent-emerald)]" />
              )}
              <span className={stock.promoter_change < 0 ? 'text-[var(--color-accent-red)]' : 'text-[var(--color-accent-emerald)]'}>
                {stock.promoter_change?.toFixed(2)}%
              </span>
            </div>
            {stock.market_cap && stock.market_cap !== 'N/A' && (
              <div>
                <span className="text-[var(--color-text-muted)]">MCap: </span>
                <span className="text-[var(--color-text-secondary)]">{stock.market_cap}</span>
              </div>
            )}
          </div>
        </Link>

        {/* Right: Verdict + Watchlist */}
        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={`text-xs font-bold ${verdictColors[stock.verdict] || 'text-[var(--color-text-secondary)]'}`}>
            {stock.verdict_icon} {stock.verdict}
          </span>
          {onToggleWatchlist && (
            <button
              onClick={(e) => { e.preventDefault(); onToggleWatchlist(stock.ticker, stock.in_watchlist); }}
              className="p-1.5 rounded-lg hover:bg-white/10 transition"
              title={stock.in_watchlist ? 'Remove from watchlist' : 'Add to watchlist'}
            >
              {stock.in_watchlist ? (
                <Eye className="w-4 h-4 text-[var(--color-accent-blue)]" />
              ) : (
                <EyeOff className="w-4 h-4 text-[var(--color-text-muted)]" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
