import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './styles/global.css';

import LoginPage    from './pages/LoginPage';
import SignupPage   from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import NotesPage    from './pages/NotesPage';
import AICoachPage  from './pages/AICoachPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<Navigate to="/login" replace />} />
        <Route path="/login"      element={<LoginPage />} />
        <Route path="/signup"     element={<SignupPage />} />
        <Route path="/dashboard"  element={<DashboardPage />} />
        <Route path="/notes"      element={<NotesPage />} />
        <Route path="/ai-coach"   element={<AICoachPage />} />
        <Route path="*"           element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
