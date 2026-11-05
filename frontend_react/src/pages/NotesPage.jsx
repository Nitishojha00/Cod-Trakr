import { useState, useEffect, useRef } from 'react';
import { AppShell } from '../components/Layout';
import api from '../api';

/* ── tiny helpers ── */
function Stars({ count }) {
  return (
    <span>
      {[1,2,3].map(i => (
        <span key={i} className={i <= count ? 'star' : 'star-empty'}>★</span>
      ))}
    </span>
  );
}

function Spinner() {
  return <div className="spinner" style={{ display: 'inline-block' }} />;
}

/* ── sidebar extra: filters + new problem ── */
function NotesSidebarContent({ onFilter, onNew, onFilterStars }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '16px' }}>
      <span className="sidebar-section-label">Filter</span>
      {[3, 2, 1, 0].map(s => (
        <button
          key={s}
          className="nav-item"
          onClick={() => onFilterStars(s)}
          style={{ fontSize: '12.5px' }}
        >
          <span style={{ color: 'var(--gold)' }}>{'★'.repeat(s) || '—'}</span>
          {s === 0 ? ' Unrated' : ` ${s} star${s > 1 ? 's' : ''}`}
        </button>
      ))}
      <div style={{ borderTop: '1px solid var(--border)', margin: '10px 0' }} />
      <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={onNew}>
        + New problem
      </button>
    </div>
  );
}

/* ── create / edit modal ── */
function ProblemModal({ initial, onClose, onSaved }) {
  const isEdit = !!initial?.problemId;
  const [form, setForm] = useState({
    problemName: initial?.problemName || '',
    problemLink: initial?.problemLink || '',
    tags: Array.isArray(initial?.tags) ? initial.tags.join(', ') : '',
    stars: initial?.stars ?? 0,
    problemDescription: initial?.problemDescription || '',
    notes: initial?.notes || '',
    mistake: initial?.mistake || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }));

  async function save(e) {
    e.preventDefault();
    if (!form.problemName.trim()) { setError('Problem name is required.'); return; }
    setLoading(true);
    setError('');
    const payload = {
      ...form,
      stars: parseInt(form.stars),
      tags: form.tags.split(',').map(t => t.trim()).filter(Boolean),
    };
    try {
      if (isEdit) {
        await api.put(`/api/notes/problem/${initial.problemId}`, payload);
      } else {
        await api.post('/api/notes/new', payload);
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || 'Operation failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-header">
          <span className="modal-title">{isEdit ? 'Edit problem' : 'Add problem'}</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {error && <div className="error-box" style={{ marginBottom: '14px' }}>{error}</div>}

        <form onSubmit={save}>
          <div className="form-row">
            <div>
              <label className="form-label">Problem name *</label>
              <input value={form.problemName} onChange={set('problemName')} placeholder="Two Sum" autoFocus />
            </div>
            <div>
              <label className="form-label">Problem link</label>
              <input type="url" value={form.problemLink} onChange={set('problemLink')} placeholder="https://leetcode.com/…" />
            </div>
          </div>

          <div className="form-row">
            <div>
              <label className="form-label">Tags (comma separated)</label>
              <input value={form.tags} onChange={set('tags')} placeholder="array, hashmap" />
            </div>
            <div>
              <label className="form-label">Importance</label>
              <select value={form.stars} onChange={set('stars')}>
                <option value="0">0 — Unrated</option>
                <option value="1">1 — Low</option>
                <option value="2">2 — Medium</option>
                <option value="3">3 — High</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea value={form.problemDescription} onChange={set('problemDescription')} rows={2} placeholder="Brief description…" />
          </div>

          <div className="form-group">
            <label className="form-label">Solution / Notes</label>
            <textarea value={form.notes} onChange={set('notes')} rows={4} placeholder="Approach, key observations…" />
          </div>

          <div className="form-group">
            <label className="form-label">Mistakes to avoid</label>
            <textarea value={form.mistake} onChange={set('mistake')} rows={2} placeholder="Common pitfalls…" />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '10px', marginTop: '4px', opacity: loading ? 0.6 : 1 }}
            disabled={loading}
          >
            {loading ? 'Saving…' : isEdit ? 'Update problem' : 'Save problem'}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── view detail modal ── */
function ViewModal({ problem, onClose, onEdit, onDeleted }) {
  const { problemId, problemName, problemLink, stars, tags, problemDescription, notes, mistake } = problem;
  const [deleting, setDeleting] = useState(false);

  async function deleteProblem() {
    if (!window.confirm('Delete this problem?')) return;
    setDeleting(true);
    try {
      await api.delete(`/api/notes/problem/${problemId}`);
      onDeleted();
      onClose();
    } catch { setDeleting(false); }
  }

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box modal-lg">
        <div className="view-modal-header">
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
              <h2 className="view-modal-title">{problemName}</h2>
              <Stars count={stars} />
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>#{problemId}</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
              {(Array.isArray(tags) ? tags : []).map(t => (
                <span className="tag" key={t}>{t}</span>
              ))}
            </div>
          </div>
          <button className="modal-close" style={{ fontSize: '24px' }} onClick={onClose}>×</button>
        </div>

        <div className="view-modal-body">
          <div className="view-actions">
            {problemLink && (
              <a href={problemLink} target="_blank" rel="noreferrer" className="btn btn-primary">
                Solve problem ↗
              </a>
            )}
            <button className="btn" onClick={() => { onClose(); onEdit(problem); }}>Edit</button>
            <button className="btn btn-danger" onClick={deleteProblem} disabled={deleting}>
              {deleting ? 'Deleting…' : 'Delete'}
            </button>
          </div>

          {problemDescription && (
            <div>
              <div className="view-section-label">Description</div>
              <p className="view-text">{problemDescription}</p>
            </div>
          )}

          <div className="note-block">
            <div className="view-section-label">Notes</div>
            <p className="view-text">{notes || 'No notes yet.'}</p>
          </div>

          {mistake && (
            <div className="mistake-block">
              <div className="view-section-label" style={{ color: 'var(--danger)' }}>Mistakes to avoid</div>
              <p className="view-text" style={{ color: '#fca5a5' }}>{mistake}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── main page ── */
export default function NotesPage() {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewState, setViewState] = useState({ view: 'importance', tag: '', stars: 0 });
  const [searchVal, setSearchVal] = useState('');
  const [createModal, setCreateModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [viewTarget, setViewTarget] = useState(null);
  const [pageTitle, setPageTitle] = useState('Top priority');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => { fetchData(viewState, page); }, []);

  async function fetchData(state = viewState, p = page) {
    setLoading(true);
    let url = '';
    const params = { page: p };

    switch (state.view) {
      case 'importance': url = '/api/notes/problemByImportance'; break;
      case 'all':        url = '/api/notes/problem';             break;
      case 'tag':        url = `/api/notes/tag/${state.tag}`;    break;
      case 'stars':      url = `/api/notes/stars/${state.stars}`; break;
      default:           url = '/api/notes/problemByImportance'; break;
    }

    try {
      const res = await api.get(url, { params });
      if (res.data.success) {
        setProblems(res.data.data || []);
        setTotalPages(res.data.totalPages || 1);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function switchView(view, extra = {}) {
    const s = { view, tag: extra.tag || '', stars: extra.stars ?? 0 };
    setViewState(s);
    setPage(1);
    fetchData(s, 1);
    // title
    if (view === 'importance') setPageTitle('Top priority');
    else if (view === 'all') setPageTitle('All problems');
    else if (view === 'tag') setPageTitle(`Tag: "${extra.tag}"`);
    else if (view === 'stars') setPageTitle(extra.stars === 0 ? 'Unrated problems' : `${extra.stars}-star problems`);
  }

  function changePage(delta) {
    const p = Math.max(1, page + delta);
    setPage(p);
    fetchData(viewState, p);
  }

  function handleSearch(e) {
    if (e.key === 'Enter' && searchVal.trim()) {
      switchView('tag', { tag: searchVal.trim() });
    }
  }

  async function openView(id) {
    try {
      const res = await api.get(`/api/notes/problemById/${id}`);
      if (res.data.success) setViewTarget(res.data.data);
    } catch {}
  }

  async function openEdit(problemOrId) {
    if (typeof problemOrId === 'object') { setEditTarget(problemOrId); return; }
    try {
      const res = await api.get(`/api/notes/problemById/${problemOrId}`);
      if (res.data.success) setEditTarget(res.data.data);
    } catch {}
  }

  const sidebarExtra = (
    <NotesSidebarContent
      onNew={() => { setCreateModal(true); setSidebarOpen(false); }}
      onFilterStars={s => { switchView('stars', { stars: s }); setSidebarOpen(false); }}
    />
  );

  return (
    <AppShell sidebarExtra={sidebarExtra}>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <h1 className="page-title">{pageTitle}</h1>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              className="btn"
              style={{ fontSize: '12px', padding: '5px 12px' }}
              onClick={() => switchView('importance')}
            >
              Top priority
            </button>
            <button
              className="btn"
              style={{ fontSize: '12px', padding: '5px 12px' }}
              onClick={() => switchView('all')}
            >
              All
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div className="search-box">
            <svg className="search-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.3"/>
              <line x1="9.5" y1="9.5" x2="13" y2="13" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
            <input
              ref={searchRef}
              value={searchVal}
              onChange={e => setSearchVal(e.target.value)}
              onKeyDown={handleSearch}
              placeholder="Search by tag…"
            />
          </div>
          <button className="btn btn-primary" onClick={() => setCreateModal(true)}>
            + New
          </button>
        </div>
      </div>

      <div style={{ padding: '20px 28px' }}>
        {loading ? (
          <div className="loader-row"><Spinner /></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '5%' }}>ID</th>
                    <th style={{ width: '35%' }}>Problem</th>
                    <th style={{ width: '25%' }}>Tags</th>
                    <th style={{ width: '15%' }}>Importance</th>
                    <th style={{ width: '8%' }}>Link</th>
                    <th style={{ width: '12%' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {problems.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                        No problems found.
                      </td>
                    </tr>
                  ) : problems.map(p => (
                    <tr
                      key={p.problemId}
                      className="clickable"
                      onClick={() => openView(p.problemId)}
                    >
                      <td style={{ color: 'var(--text-dim)', fontSize: '12px' }}>#{p.problemId}</td>
                      <td style={{ fontWeight: 500, color: 'var(--text)' }}>{p.problemName}</td>
                      <td>
                        {(Array.isArray(p.tags) ? p.tags : []).map(t => (
                          <span className="tag" key={t}>{t}</span>
                        ))}
                      </td>
                      <td><Stars count={p.stars} /></td>
                      <td onClick={e => e.stopPropagation()}>
                        {p.problemLink && (
                          <a
                            href={p.problemLink}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: 'var(--text-dim)', fontSize: '14px' }}
                            title="Open problem"
                          >
                            ↗
                          </a>
                        )}
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <button
                            className="btn"
                            style={{ padding: '4px 9px', fontSize: '12px' }}
                            onClick={() => openEdit(p.problemId)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '4px 9px', fontSize: '12px' }}
                            onClick={async () => {
                              if (!window.confirm('Delete this problem?')) return;
                              await api.delete(`/api/notes/problem/${p.problemId}`);
                              fetchData(viewState, page);
                            }}
                          >
                            Del
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <button className="btn" onClick={() => changePage(-1)} disabled={page <= 1}>← Prev</button>
              <span className="page-indicator">Page {page} / {totalPages}</span>
              <button className="btn" onClick={() => changePage(1)} disabled={page >= totalPages}>Next →</button>
            </div>
          </>
        )}
      </div>

      {createModal && (
        <ProblemModal
          initial={null}
          onClose={() => setCreateModal(false)}
          onSaved={() => fetchData(viewState, page)}
        />
      )}

      {editTarget && (
        <ProblemModal
          initial={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={() => fetchData(viewState, page)}
        />
      )}

      {viewTarget && (
        <ViewModal
          problem={viewTarget}
          onClose={() => setViewTarget(null)}
          onEdit={p => { setViewTarget(null); setEditTarget(p); }}
          onDeleted={() => fetchData(viewState, page)}
        />
      )}
    </AppShell>
  );
}
