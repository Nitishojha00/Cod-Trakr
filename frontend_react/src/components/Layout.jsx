import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import api from '../api';

function IconDashboard() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <rect x="1" y="1" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="8.5" y="1" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="1" y="8.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
    </svg>
  );
}

function IconNotes() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <rect x="2" y="1" width="11" height="13" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
      <line x1="5" y1="5" x2="10" y2="5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="5" y1="7.5" x2="10" y2="7.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="5" y1="10" x2="8" y2="10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function IconAI() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <circle cx="7.5" cy="7.5" r="6" stroke="currentColor" strokeWidth="1.2"/>
      <circle cx="7.5" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.2"/>
      <line x1="7.5" y1="1.5" x2="7.5" y2="5.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="7.5" y1="9.5" x2="7.5" y2="13.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="1.5" y1="7.5" x2="5.5" y2="7.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="9.5" y1="7.5" x2="13.5" y2="7.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function IconLogout() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M9 2H11.5C12.05 2 12.5 2.45 12.5 3V11C12.5 11.55 12.05 12 11.5 12H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <path d="M6 9.5L9 7L6 4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="1.5" y1="7" x2="9" y2="7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function IconMenu() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="2" y1="12" x2="14" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

export function Sidebar({ open, onClose, extraContent }) {
  const navigate = useNavigate();

  async function logout() {
    try { await api.post('/logout'); } catch (_) {}
    navigate('/login');
  }

  return (
    <>
      {open && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'rgba(0,0,0,0.5)' }}
          onClick={onClose}
        />
      )}
      <aside className={`sidebar${open ? ' open' : ''}`}>
        <NavLink to="/dashboard" className="sidebar-brand" onClick={onClose}>
          <span className="brand-dot" />
          COD TRAKR
        </NavLink>

        <nav className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            onClick={onClose}
          >
            <IconDashboard /> Dashboard
          </NavLink>
          <NavLink
            to="/notes"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            onClick={onClose}
          >
            <IconNotes /> Notes
          </NavLink>
          <NavLink
            to="/ai-coach"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            onClick={onClose}
          >
            <IconAI /> AI Coach
          </NavLink>
        </nav>

        {extraContent}

        <div className="sidebar-bottom">
          <button className="btn-logout" onClick={logout}>
            <IconLogout /> Log out
          </button>
        </div>
      </aside>
    </>
  );
}

export function AppShell({ children, sidebarExtra }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <button className="mobile-toggle" onClick={() => setSidebarOpen(true)}>
        <IconMenu />
      </button>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        extraContent={sidebarExtra}
      />
      <main className="main">{children}</main>
    </div>
  );
}
