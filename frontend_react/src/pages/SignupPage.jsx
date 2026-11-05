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

export default function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [signupId, setSignupId] = useState(null);
  const [otpSent, setOtpSent] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'error'|'success', msg }
  const [loading, setLoading] = useState(false);

  async function generateOTP() {
    if (!name || !email || !password) {
      setStatus({ type: 'error', msg: 'Please fill in all fields.' });
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const res = await api.post('/api/auth/signup-generate-otp', { name, email, password });
      setSignupId(res.data.signupId);
      setOtpSent(true);
      setStatus({ type: 'success', msg: `OTP sent to ${email}` });
    } catch (err) {
      const msg = err.response?.data;
      setStatus({
        type: 'error',
        msg: msg === 'User already registered'
          ? 'An account with this email already exists.'
          : (typeof msg === 'string' ? msg : 'Failed to send OTP.'),
      });
    } finally {
      setLoading(false);
    }
  }

  async function verifyOTP() {
    if (!otp) { setStatus({ type: 'error', msg: 'Enter the OTP sent to your email.' }); return; }
    setLoading(true);
    setStatus(null);
    try {
      await api.post('/api/auth/signup-verify-otp', { signupId, otp });
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data;
      setStatus({ type: 'error', msg: typeof msg === 'string' ? msg : 'Invalid or expired OTP.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Logo />
        <h1 className="auth-heading">Create account</h1>
        <p className="auth-sub">Track your DSA progress across platforms.</p>

        {status && (
          status.type === 'error'
            ? <div className="error-box">{status.msg}</div>
            : <div className="success-box">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <circle cx="6.5" cy="6.5" r="6" stroke="currentColor" strokeWidth="1.1"/>
                  <path d="M4 6.5L6 8.5L9.5 5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                {status.msg}
              </div>
        )}

        <div className="form-group">
          <label className="form-label">Full name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Rahul Kumar"
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@email.com"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min. 4 characters"
            autoComplete="new-password"
          />
          <small className="password-hint">
            Must contain 4+ characters, one uppercase letter,
            one lowercase letter, one number, and one symbol.
          </small>
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '10px', opacity: loading && !otpSent ? 0.6 : 1 }}
          onClick={generateOTP}
          disabled={loading && !otpSent}
        >
          {otpSent ? 'Resend OTP' : loading ? 'Sending…' : 'Send OTP →'}
        </button>

        {otpSent && (
          <>
            <hr className="auth-divider" />
            <p style={{ fontSize: '12.5px', color: 'var(--text-dim)', marginBottom: '10px' }}>
              Enter the 6-digit code sent to <strong style={{ color: 'var(--text-muted)' }}>{email}</strong>
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                placeholder="000000"
                maxLength={6}
                style={{ letterSpacing: '0.25em', textAlign: 'center', flex: 1 }}
                onKeyDown={e => e.key === 'Enter' && verifyOTP()}
              />
              <button
                className="btn btn-primary"
                style={{ padding: '8px 16px', opacity: loading ? 0.6 : 1, whiteSpace: 'nowrap' }}
                onClick={verifyOTP}
                disabled={loading}
              >
                {loading ? '…' : 'Verify →'}
              </button>
            </div>
          </>
        )}

        <div className="auth-link-row">
          Already have an account?{' '}
          <button className="auth-link" onClick={() => navigate('/login')}>Sign in</button>
        </div>
      </div>
    </div>
  );
}
