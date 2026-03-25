import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { stocksAPI } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';
import { ArrowLeft, Brain, TrendingDown, TrendingUp, AlertCircle, Info, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

export default function CompanyDetail() {
  const { ticker } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

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
  
  // Format data for chart
  const chartData = (stock?.quarters || []).map((q, idx) => ({
    name: q,
    holding: stock.all_holdings && stock.all_holdings[idx] !== undefined ? stock.all_holdings[idx] : null,
    price: stock.all_prices && stock.all_prices[idx] !== undefined ? stock.all_prices[idx] : null
  }));

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
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition">
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
          <div className="text-4xl font-light mb-2">{(stock.promoter_current || 0).toFixed(2)}%</div>
          <div className={`flex items-center gap-1.5 font-medium ${(stock.promoter_change || 0) < 0 ? 'text-[var(--color-accent-red)]' : 'text-[var(--color-accent-emerald)]'}`}>
            {(stock.promoter_change || 0) < 0 ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
            {Math.abs(stock.promoter_change || 0).toFixed(2)}% change
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <div className="lg:col-span-2 glass-card p-6 min-h-[400px]">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-[var(--color-accent-blue)]" />
            Holding Trend History
          </h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--color-text-muted)" fontSize={12} tickMargin={10} />
                <YAxis yAxisId="left" domain={[0, 100]} stroke="var(--color-accent-blue)" fontSize={12} tickFormatter={val => `${val}%`} />
                <YAxis yAxisId="right" orientation="right" domain={['auto', 'auto']} stroke="var(--color-accent-amber)" fontSize={12} tickFormatter={val => `₹${val}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-bg-card)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '13px' }}
                  labelStyle={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }}/>
                <Line yAxisId="left" type="monotone" dataKey="holding" name="Promoter Holding (%)" stroke="var(--color-accent-blue)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                {chartData.some(d => d.price) && (
                  <Line yAxisId="right" type="monotone" dataKey="price" name="Stock Price (₹)" stroke="var(--color-accent-amber)" strokeWidth={2} dot={{ r: 4 }} />
                )}
              </LineChart>
            </ResponsiveContainer>
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
                 <span className="font-medium text-[var(--color-text-primary)]">{analysis?.trend_type || 'N/A'}</span>
               </div>
               <div className="flex justify-between items-center py-2 border-b border-[var(--color-border)] text-sm">
                 <span className="text-[var(--color-text-secondary)]">Retail Involvement</span>
                 <span className="font-medium text-[var(--color-text-primary)]">{analysis?.retail_trend || 'N/A'}</span>
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
