import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Lock, User, UserCircle, ArrowRight } from 'lucide-react';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await signup(username, password, displayName);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account. Username might be taken.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Activity className="w-10 h-10 text-[var(--color-accent-blue)]" />
            <h1 className="text-3xl font-bold text-gradient">PromoterAI</h1>
          </div>
          <p className="text-[var(--color-text-secondary)]">Create a new account</p>
        </div>

        <div className="glass-card p-6 sm:p-8">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-[var(--color-accent-red)]/10 border border-[var(--color-accent-red)]/20 text-[var(--color-accent-red)] text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
                Display Name (Optional)
              </label>
              <div className="relative">
                <UserCircle className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-10 pr-4 py-2.5 text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)] transition"
                  placeholder="How should we call you?"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-10 pr-4 py-2.5 text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)] transition"
                  placeholder="Choose a username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg pl-10 pr-4 py-2.5 text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent-blue)] transition"
                  placeholder="Create a strong password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-[var(--color-accent-blue)] hover:bg-blue-600 text-white rounded-lg font-medium transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? 'Creating Account...' : 'Sign Up'}
              {!isLoading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
            Already have an account?{' '}
            <Link to="/login" className="text-[var(--color-accent-blue)] hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
