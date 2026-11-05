import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/Layout';
import api from '../api';

function Spinner() {
  return <div className="spinner" style={{ margin: '0 auto' }} />;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState('');
  const [accounts, setAccounts] = useState({ lc: '', cf: '', cc: '', gfg: '' });
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => { loadUser(); }, []);

  async function loadUser() {
    try {
      const res = await api.get('/api/dashboard/me');
      setUser(res.data.name);
      const p = res.data.platforms || {};
      setAccounts({
        lc: p.LeetCode?.username || '',
        cf: p.Codeforces?.username || '',
        cc: p.CodeChef?.username || '',
        gfg: p.GFG?.username || '',
      });
      await loadStats();
    } catch {
      navigate('/login');
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    setStatsLoading(true);
    try {
      const res = await api.get('/api/dashboard/dashboard');
      setStats(res.data);
    } catch {
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }

  async function saveAccounts() {
    setSaving(true);
    setMsg(null);
    const platforms = {};
    if (accounts.lc)  platforms.LeetCode   = { username: accounts.lc };
    if (accounts.cf)  platforms.Codeforces = { username: accounts.cf };
    if (accounts.cc)  platforms.CodeChef   = { username: accounts.cc };
    if (accounts.gfg) platforms.GFG        = { username: accounts.gfg };
    try {
      await api.post('/api/dashboard/accounts', { platforms });
      setMsg({ type: 'success', text: 'Accounts saved.' });
      await loadStats();
    } catch {
      setMsg({ type: 'error', text: 'Failed to save accounts.' });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="loader-row"><Spinner /></div>
      </AppShell>
    );
  }

  const totalSolved   = stats?.totalSolved   ?? 0;
  const totalContests = stats?.totalContests ?? 0;
  const bestRating    = stats?.bestRating    ?? 0;
  const platformCount = stats?.platformCount ?? 0;
  const platforms     = stats?.platforms     ?? {};

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>
          Welcome back, <strong style={{ color: 'var(--text-muted)' }}>{user}</strong>
        </span>
      </div>

      <div className="dash-page">
        {/* ── Overall stats ── */}
        <div className="section-title">Overview</div>
        <div className="dash-stats">
          <StatCard label="Problems solved" value={totalSolved} />
          <StatCard label="Contests" value={totalContests} />
          <StatCard label="Best rating" value={bestRating} />
          <StatCard label="Platforms" value={platformCount} />
        </div>

        {/* ── Link accounts ── */}
        <div className="section-title">Linked accounts</div>
        <div className="accounts-form">
          <p style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '14px' }}>
            Enter your username only — not the full profile URL.
          </p>
          {msg && (
            <div className={msg.type === 'error' ? 'error-box' : 'success-box'} style={{ marginBottom: '12px' }}>
              {msg.text}
            </div>
          )}
          <div className="accounts-inputs">
            {[
              { key: 'lc',  label: 'LeetCode' },
              { key: 'cf',  label: 'Codeforces' },
              { key: 'cc',  label: 'CodeChef' },
              { key: 'gfg', label: 'GFG' },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="form-label">{label}</label>
                <input
                  type="text"
                  value={accounts[key]}
                  onChange={e => setAccounts(a => ({ ...a, [key]: e.target.value }))}
                  placeholder={`${label} username`}
                />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" onClick={saveAccounts} disabled={saving}>
            {saving ? 'Saving…' : 'Save accounts'}
          </button>
        </div>

        {/* ── Platform breakdown ── */}
        <div className="section-title">Platform breakdown</div>
        {statsLoading ? (
          <div className="loader-row"><Spinner /></div>
        ) : Object.keys(platforms).filter(k => platforms[k]?.username).length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-dim)', padding: '10px 0' }}>
            No platforms linked yet. Add your usernames above.
          </p>
        ) : (
          <div className="platform-grid">
            {Object.entries(platforms).filter(([, p]) => p?.username).map(([name, p]) => (
              <div className="platform-card" key={name}>
                <div className="platform-name">{name}</div>
                {p.profile && (
                  <p style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '12px' }}>
                    {p.profile}
                  </p>
                )}
                <div className="platform-stats">
                  <PlatStat label="Solved"   value={p.solved   ?? 0} />
                  <PlatStat label="Contests" value={p.contests ?? 0} />
                  <PlatStat label="Rating"   value={p.rating   ?? 0} />
                  <PlatStat label="Rank"     value={p.rank     ?? '—'} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function PlatStat({ label, value }) {
  return (
    <div className="platform-stat">
      <div className="platform-stat-label">{label}</div>
      <div className="platform-stat-value">{value}</div>
    </div>
  );
}
