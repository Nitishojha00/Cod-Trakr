import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function Logo() {
  return (
    <div className="auth-logo">
      <span className="auth-logo-dot" />
      COD TRAKR
    </div>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function login() {
    if (!email || !password) { setError('Enter your email and password.'); return; }
    setLoading(true);
    setError('');
    try {
      await api.post('/api/auth/login', { email, password });
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data;
      setError(typeof msg === 'string' ? msg : 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Logo />
        <h1 className="auth-heading">Welcome back</h1>
        <p className="auth-sub">Sign in to your account.</p>

        {error && <div className="error-box">{error}</div>}

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@email.com"
            autoFocus
            onKeyDown={e => e.key === 'Enter' && login()}
          />
        </div>

        <div className="form-group" style={{ position: 'relative' }}>
          <label className="form-label">Password</label>
          <input
            type={showPass ? 'text' : 'password'}
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Your password"
            style={{ paddingRight: '60px' }}
            onKeyDown={e => e.key === 'Enter' && login()}
          />
          <button
            onClick={() => setShowPass(s => !s)}
            style={{
              position: 'absolute', right: '10px', bottom: '9px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-dim)', fontSize: '11px', padding: '2px 4px',
            }}
            tabIndex={-1}
          >
            {showPass ? 'Hide' : 'Show'}
          </button>
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '10px', marginTop: '4px', opacity: loading ? 0.6 : 1 }}
          onClick={login}
          disabled={loading}
        >
          {loading ? 'Signing in…' : 'Sign in →'}
        </button>

        <div className="auth-link-row">
          New here?{' '}
          <button className="auth-link" onClick={() => navigate('/signup')}>
            Create account
          </button>
        </div>
      </div>
    </div>
  );
}
