import { useState, useEffect, useRef } from 'react';
import { AppShell } from '../components/Layout';
import api from '../api';
import { marked } from 'marked';

const STARTERS = [
  'Analyze my profile',
  'How to improve my rating?',
  'Give me a 30-day plan',
  'What topics should I study?',
  'I solve mostly easy problems',
];

function StatusDot() {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#4ade80' }}>
      <span
        style={{
          width: '6px', height: '6px', borderRadius: '50%', background: '#4ade80',
          animation: 'pulse 2s infinite',
        }}
      />
      Online
    </span>
  );
}

function AIClearBtn({ onClear }) {
  return (
    <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
      <button
        className="nav-item"
        style={{ fontSize: '12.5px', color: 'var(--text-dim)', width: '100%' }}
        onClick={onClear}
      >
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <polyline points="2,3.5 11,3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          <path d="M5 3.5V2.5C5 2.22 5.22 2 5.5 2h2C7.78 2 8 2.22 8 2.5V3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          <path d="M3.5 3.5l.5 7h5l.5-7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Clear chat
      </button>
    </div>
  );
}

export default function AICoachPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const [toast, setToast] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => { init(); }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function init() {
    try {
      const res = await api.get('/api/dashboard/dashboard');
      setStats(res.data);
    } catch {}

    try {
      const res = await api.get('/api/chat/history');
      const { history } = res.data;
      if (history?.length) {
        setMessages(history.map(m => ({
          role: m.role === 'user' ? 'user' : 'ai',
          text: m.parts[0].text,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        })));
      }
    } catch {}
  }

  async function sendMessage(text = input.trim()) {
    if (!text || loading) return;
    setLoading(true);
    setInput('');
    autoResize(null);

    const userMsg = { role: 'user', text, time: now() };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await api.post('/api/chat/send', { message: text });
      setMessages(prev => [...prev, { role: 'ai', text: res.data.reply, time: now() }]);
    } catch (err) {
      const msg = err.response?.data?.message || 'Something went wrong.';
      showToast('Error: ' + msg);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  async function clearChat() {
    setConfirmClear(false);
    try {
      await api.delete('/api/chat/clear');
      setMessages([]);
      showToast('Chat cleared.');
    } catch {
      showToast('Failed to clear chat.');
    }
  }

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  }

  function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function autoResize(e) {
    const el = e?.target || textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  const sidebarExtra = <AIClearBtn onClear={() => setConfirmClear(true)} />;

  return (
    <AppShell sidebarExtra={sidebarExtra}>
      {/* header */}
      <div className="page-header">
        <div>
          <h1 className="page-title" style={{ marginBottom: '2px' }}>AI Coach</h1>
          {stats && (
            <p style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
              {stats.totalSolved} solved · {stats.totalContests} contests · best rating {stats.bestRating}
            </p>
          )}
        </div>
        <StatusDot />
      </div>

      {/* chat area */}
      <div className="chat-shell">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div style={{ fontSize: '36px' }}>◎</div>
              <p className="chat-empty-title">Your personal coding coach</p>
              <p className="chat-empty-sub">
                Ask me anything about your DSA progress, weak spots, or how to improve your contest rating.
              </p>
              <div className="chip-row">
                {STARTERS.map(s => (
                  <button key={s} className="chip" onClick={() => sendMessage(s)}>{s}</button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => <MessageRow key={i} message={m} />)
          )}

          {loading && (
            <div className="message-row ai">
              <div className="msg-avatar">◎</div>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* input */}
        <div className="chat-input-area">
          <div className="chat-input-wrap">
            <textarea
              ref={textareaRef}
              className="chat-textarea"
              value={input}
              onChange={e => { setInput(e.target.value); autoResize(e); }}
              onKeyDown={handleKeyDown}
              placeholder="Ask your coach anything…"
              rows={1}
              maxLength={1000}
            />
            <button
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              title="Send"
            >
              ↑
            </button>
          </div>
          <div className="chat-hint">
            <span>Enter ↵ to send · Shift+Enter for new line</span>
            <span>{input.length} / 1000</span>
          </div>
        </div>
      </div>

      {/* confirm clear modal */}
      {confirmClear && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: '400px', textAlign: 'center' }}>
            <p style={{ fontWeight: 600, color: 'var(--text)', marginBottom: '8px', fontSize: '16px' }}>
              Clear conversation?
            </p>
            <p style={{ fontSize: '13px', color: 'var(--text-dim)', marginBottom: '22px' }}>
              This will permanently delete your chat history with the AI Coach.
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn" style={{ flex: 1 }} onClick={() => setConfirmClear(false)}>Cancel</button>
              <button className="btn btn-danger" style={{ flex: 1 }} onClick={clearChat}>Yes, clear</button>
            </div>
          </div>
        </div>
      )}

      {/* toast */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: '28px', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--bg-card)', border: '1px solid var(--border-md)',
          borderRadius: 'var(--radius-sm)', padding: '9px 18px',
          fontSize: '12.5px', color: 'var(--text-muted)',
          boxShadow: '0 4px 16px rgba(0,0,0,0.5)', zIndex: 999,
          whiteSpace: 'nowrap',
        }}>
          {toast}
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
      `}</style>
    </AppShell>
  );
}

function MessageRow({ message }) {
  const { role, text, time } = message;

  const content =
    role === 'ai'
      ? marked.parse(text)
      : text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');

  return (
    <div className={`message-row ${role}`}>
      <div className="msg-avatar">{role === 'user' ? '◇' : '◎'}</div>
      <div>
        <div
          className="msg-bubble"
          dangerouslySetInnerHTML={{ __html: content }}
        />
        <div className="msg-time">{time}</div>
      </div>
    </div>
  );
}
