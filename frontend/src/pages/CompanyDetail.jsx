import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { stocksAPI } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';
import { ArrowLeft, Brain, TrendingDown, TrendingUp, AlertCircle, Info, Activity, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

export default function CompanyDetail() {
  const { ticker } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('1Y');

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        const res = await stocksAPI.detail(ticker);
        setData(res.data);
      } catch (err) {
        toast.error('Failed to load company details');
      } finally {
        setLoading(false);
      }
    };
    fetchCompany();
  }, [ticker]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-[var(--color-accent-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!data?.found) return <div className="p-8 text-center text-[var(--color-text-secondary)]">Company not found or not yet scanned.</div>;

  const stock = data.data;
  const analysis = stock?.analysis || {};
  const histories = (stock?.holdings_history || []).slice().sort((a, b) => new Date(a.scanned_at) - new Date(b.scanned_at));
  
  // Format data for holding chart
  const holdingData = (stock?.quarters || []).map((q, idx) => ({
    name: q,
    holding: stock.all_holdings && stock.all_holdings[idx] !== undefined ? stock.all_holdings[idx] : null,
  }));

  // Safe formatter for numbers
  const safeFixed = (v, dec = 1) => {
    const num = Number(v);
    return isNaN(num) ? '—' : num.toFixed(dec);
  };

  // Mock daily price data for the Area Chart based on the quarterly prices since we don't have daily JSON data in mock DB
  // In production, this would use a real daily timeseries from the backend
  const generatePriceData = () => {
    const dataPoints = timeFilter === '1W' ? 7 : timeFilter === '1M' ? 30 : timeFilter === '3M' ? 90 : 365;
    
    const hasPrices = stock?.all_prices && stock.all_prices.length > 0;
    const lastPrice = stock?.current_price || (hasPrices ? stock.all_prices[stock.all_prices.length - 1] : 1540.50);
    const basePrice = Number(lastPrice) || 1540.50;
    
    // Generate realistic looking walk sequence
    let currentPrice = hasPrices ? (Number(stock.all_prices[0]) || basePrice) : (basePrice * 0.7);
    const result = [];
    const now = new Date();
    
    // Create deterministic random based on ticker string so it doesn't jump wildly on every re-render
    let seed = stock?.ticker ? stock.ticker.charCodeAt(0) + stock.ticker.charCodeAt(stock.ticker.length-1) : 42;
    const random = () => {
      const x = Math.sin(seed++) * 10000;
      return x - Math.floor(x);
    };
    
    for (let i = dataPoints; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Add random walk volatility (slight upward bias overall)
      const volatility = currentPrice * (random() * 0.05 - 0.02);
      currentPrice = Math.max(1, currentPrice + volatility);
      
      // Every 90 days, sync back to quarterly historical price if available
      if (hasPrices && i % 90 === 0) {
        const quarterIdx = Math.max(0, stock.all_prices.length - 1 - Math.floor(i / 90));
        if (stock.all_prices[quarterIdx]) {
           currentPrice = (currentPrice + Number(stock.all_prices[quarterIdx])) / 2;
        }
      }
      
      result.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        price: Number(currentPrice.toFixed(2))
      });
    }
    
    if (result.length > 0) {
      result[result.length - 1].price = Number(basePrice.toFixed(2));
    }
    return result;
  };
  
  const priceData = generatePriceData();

  const riskClass = {
    High: 'bg-red-500/10 text-red-500',
    Medium: 'bg-amber-500/10 text-amber-500',
    Low: 'bg-emerald-500/10 text-emerald-500',
  }[analysis?.risk_level || 'Low'] || 'bg-emerald-500/10 text-emerald-500';

  const verdictColors = {
    Exit: 'text-[var(--color-verdict-exit)] bg-[var(--color-verdict-exit)]/10',
    Caution: 'text-[var(--color-verdict-caution)] bg-[var(--color-verdict-caution)]/10',
    Hold: 'text-[var(--color-verdict-hold)] bg-[var(--color-verdict-hold)]/10',
    Buy: 'text-[var(--color-verdict-buy)] bg-[var(--color-verdict-buy)]/10',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-accent-blue)] transition font-medium">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      {/* Header Info */}
      <div className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight">{stock.ticker}</h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${riskClass}`}>
              {analysis?.risk_level || 'Low'} Risk ({analysis?.risk_score || 50}/100)
            </span>
          </div>
          <p className="text-[var(--color-text-secondary)] text-lg">{stock.company_name}</p>
          <div className="flex gap-4 mt-4 text-sm text-[var(--color-text-muted)]">
            <span>Market Cap: <strong className="text-[var(--color-text-primary)]">{stock.market_cap || 'N/A'}</strong></span>
            <span>Exchange: <strong className="text-[var(--color-text-primary)]">{stock.exchange || 'NSE'}</strong></span>
          </div>
        </div>
        
        <div className="flex flex-col items-end shrink-0">
          <div className="text-sm text-[var(--color-text-secondary)] mb-1">Current Promoter Holding</div>
          <div className="text-4xl font-light mb-2">
            {safeFixed(stock.promoter_current, 2)}%
          </div>
          <div className={`flex items-center gap-1.5 font-medium ${Number(stock.promoter_change) < 0 ? 'text-[var(--color-accent-red)]' : 'text-[var(--color-accent-emerald)]'}`}>
            {Number(stock.promoter_change) < 0 ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
            {stock.promoter_change !== 'Pending' && stock.promoter_change !== undefined 
              ? `${safeFixed(Math.abs(Number(stock.promoter_change)), 2)}% change` 
              : 'Pending'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Charts */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Price Tracking Area Chart */}
          <div className="glass-card p-6 border-t-2 border-t-[var(--color-accent-blue)]">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-[var(--color-accent-blue)]" />
                Stock Price Trend
              </h2>
              <div className="flex bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-1">
                {['1W', '1M', '3M', '1Y'].map(tf => (
                  <button
                    key={tf}
                    onClick={() => setTimeFilter(tf)}
                    className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                      timeFilter === tf 
                        ? 'bg-[var(--color-accent-blue)] text-white shadow' 
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={priceData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-accent-blue)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--color-accent-blue)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} opacity={0.5} />
                  <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={10} tickMargin={10} minTickGap={30} />
                  <YAxis stroke="var(--color-text-muted)" fontSize={10} domain={['dataMin - 10', 'dataMax + 10']} tickFormatter={val => `₹${val}`} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'var(--color-bg-card)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                    itemStyle={{ color: 'var(--color-accent-blue)', fontSize: '13px', fontWeight: 'semibold' }}
                    labelStyle={{ color: 'var(--color-text-secondary)', marginBottom: '4px', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="price" name="Price" stroke="var(--color-accent-blue)" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Holdings History Line Chart */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Clock className="w-5 h-5 text-[var(--color-accent-amber)]" />
              Promoter Holding History
            </h2>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={holdingData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} opacity={0.5} />
                  <XAxis dataKey="name" stroke="var(--color-text-muted)" fontSize={11} tickMargin={10} />
                  <YAxis domain={['dataMin - 2', 'dataMax + 2']} stroke="var(--color-text-muted)" fontSize={11} tickFormatter={val => safeFixed(val, 1) + '%'} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'var(--color-bg-card)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                    itemStyle={{ color: 'var(--color-accent-amber)', fontSize: '13px', fontWeight: 'semibold' }}
                  />
                  <Line type="monotone" dataKey="holding" name="Promoter Holding" stroke="var(--color-accent-amber)" strokeWidth={3} dot={{ r: 4, fill: 'var(--color-bg-card)', strokeWidth: 2 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* AI Analysis / Verdict */}
        <div className="space-y-6">
          <div className="glass-card p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--color-accent-purple)]/5 rounded-bl-full -z-10" />
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5 text-[var(--color-accent-purple)]" />
              AI Deep Analysis
            </h2>
            <div className="mb-6">
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-lg font-bold ${verdictColors[analysis?.verdict] || verdictColors.Hold}`}>
                {analysis?.verdict_icon || '🟡'} {analysis?.verdict || 'Hold'}
              </span>
            </div>
            
            <div className="space-y-4">
              <section>
                <h4 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1 uppercase tracking-tight">Summary</h4>
                <p className="text-[var(--color-text-secondary)] text-sm leading-relaxed">
                  {analysis?.summary || 'Scanning for detailed insights...'}
                </p>
              </section>

              {analysis?.ai_reason && (
                <section>
                  <h4 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1 uppercase tracking-tight">AI Reasoning</h4>
                  <p className="text-[var(--color-text-secondary)] text-xs leading-relaxed italic">
                    {analysis.ai_reason}
                  </p>
                </section>
              )}

              {analysis?.reasons && analysis.reasons.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-[var(--color-text-primary)] mb-2 uppercase tracking-tight">Possible Reasons</h4>
                  <ul className="grid grid-cols-1 gap-2">
                    {analysis.reasons.map((reason, i) => (
                      <li key={i} className="bg-white/5 border border-white/10 p-2 rounded text-[11px] text-[var(--color-text-secondary)] flex gap-2">
                         <span className="text-[var(--color-accent-purple)]">•</span> {reason}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
            
            {analysis?.key_factors && analysis.key_factors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-[var(--color-text-primary)]">Key Factors:</h4>
                <ul className="space-y-1.5">
                  {analysis.key_factors.map((factor, i) => (
                    <li key={i} className="text-xs text-[var(--color-text-secondary)] flex items-start gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-border-light)] mt-1 shrink-0" />
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="glass-card p-6">
             <h2 className="text-sm font-semibold mb-4 text-[var(--color-text-muted)] uppercase tracking-wider">Analysis Details</h2>
             <div className="space-y-3">
               <div className="flex justify-between items-center py-2 border-b border-[var(--color-border)] text-sm">
                 <span className="text-[var(--color-text-secondary)]">Historical Trend</span>
                 <span className="font-medium text-[var(--color-text-primary)]">{analysis?.historical_trend || 'Consistent'}</span>
               </div>
               <div className="flex justify-between items-center py-2 border-b border-[var(--color-border)] text-sm">
                 <span className="text-[var(--color-text-secondary)]">Consistency</span>
                 <span className="font-medium text-[var(--color-text-primary)]">{analysis?.consistency || 'Stable'}</span>
               </div>
               <div className="flex justify-between items-center py-2 text-sm">
                 <span className="text-[var(--color-text-secondary)]">Pledged Shares</span>
                 <span className="font-medium text-[var(--color-text-primary)]">{analysis?.pledged_percentage ? `${analysis.pledged_percentage}%` : 'Low/None'}</span>
               </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
