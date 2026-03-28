import { useState, useEffect } from 'react';
import { alertsAPI } from '../services/api';
import { Bell, Check, Trash2, ShieldAlert, Key } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [telegramChatId, setTelegramChatId] = useState('');
  const [showTelegramSetup, setShowTelegramSetup] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await alertsAPI.get();
      setAlerts(res.data.alerts || []);
    } catch (err) {
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await alertsAPI.markRead(id);
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    } catch (err) {
      toast.error('Failed to update alert');
    }
  };

  const markAllRead = async () => {
    try {
      await alertsAPI.markAllRead();
      setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
      toast.success('All alerts marked as read');
    } catch (err) {
      toast.error('Failed to update alerts');
    }
  };

  const setupTelegram = async (e) => {
    e.preventDefault();
    if (!telegramChatId) return;
    try {
      await alertsAPI.setupTelegram(telegramChatId);
      toast.success('Telegram alerts configured successfully');
      setShowTelegramSetup(false);
      setTelegramChatId('');
    } catch (err) {
      toast.error('Failed to setup Telegram alerts');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 mb-1">
            <Bell className="w-6 h-6 text-[var(--color-accent-amber)]" />
            Alerts
          </h1>
          <p className="text-[var(--color-text-secondary)] text-sm">
            Notifications about high-risk promoter selling in your watchlist
          </p>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={() => setShowTelegramSetup(!showTelegramSetup)}
            className="px-3 py-1.5 text-sm bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 rounded-lg transition"
          >
            Telegram Setup
          </button>
          
          {alerts.some(a => !a.is_read) && (
            <button 
              onClick={markAllRead}
              className="px-3 py-1.5 text-sm bg-[var(--color-bg-secondary)] hover:bg-[var(--color-bg-card-hover)] border border-[var(--color-border)] rounded-lg transition flex items-center gap-1.5"
            >
              <Check className="w-4 h-4" /> Mark all read
            </button>
          )}
        </div>
      </div>

      {showTelegramSetup && (
        <div className="glass-card p-5 mb-8 border-blue-500/30">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-blue-400" />
            Get Real-time Telegram Alerts
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            Connect your Telegram account to instantly receive notifications for High Risk alerts on your watchlisted stocks. Enter your Telegram Chat ID below.
          </p>
          <form onSubmit={setupTelegram} className="flex gap-2">
            <div className="relative flex-1 max-w-xs">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input
                type="text"
                required
                value={telegramChatId}
                onChange={e => setTelegramChatId(e.target.value)}
                placeholder="Telegram Chat ID"
                className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <button 
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
            >
              Save
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-[var(--color-accent-blue)] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map(alert => (
            <div 
              key={alert.id}
              className={`p-4 rounded-xl border transition ${
                alert.is_read 
                  ? 'bg-[var(--color-bg-secondary)]/50 border-[var(--color-border)]' 
                  : 'bg-[var(--color-bg-card)] border-[var(--color-accent-amber)]/30 glow-amber relative overflow-hidden'
              }`}
            >
              {!alert.is_read && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--color-accent-amber)]" />
              )}
              
              <div className="flex justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-[var(--color-text-primary)]">{alert.ticker}</span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                    {!alert.is_read && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-[var(--color-accent-amber)]/20 text-[var(--color-accent-amber)]">
                        New
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-[var(--color-text-secondary)]">{alert.message}</p>
                </div>
                
                {!alert.is_read && (
                  <button 
                    onClick={() => markAsRead(alert.id)}
                    className="p-2 shrink-0 text-[var(--color-text-muted)] hover:text-white hover:bg-white/10 rounded-lg transition"
                    title="Mark as read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-[var(--color-text-secondary)]">
          <Bell className="w-12 h-12 mx-auto text-[var(--color-text-muted)] mb-4 opacity-50" />
          <p>No alerts generated yet.</p>
        </div>
      )}
    </div>
  );
}
