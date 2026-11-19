import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import GrainOverlay from './components/GrainOverlay';
import NetraCareLogo from './components/NetraCareLogo';
import Home from './pages/Home';
import Login from './pages/Login';
import PatientDashboard from './pages/PatientDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import StaffDashboard from './pages/StaffDashboard';

function MainApp() {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState('home');

  // Auto-route to role dashboard on login
  useEffect(() => {
    if (user) {
      if (user.role === 'patient') setCurrentTab('patient');
      else if (user.role === 'doctor') setCurrentTab('doctor');
      else if (['staff', 'admin', 'sub_admin'].includes(user.role)) setCurrentTab('staff');
    }
  }, [user]);

  const handleLoginSuccess = (role) => {
    if (role === 'patient') setCurrentTab('patient');
    else if (role === 'doctor') setCurrentTab('doctor');
    else setCurrentTab('staff');
  };

  const handleNavigateToBook = () => {
    if (user?.role === 'patient') {
      setCurrentTab('patient');
    } else {
      setCurrentTab('login');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', width: '100%', overflowX: 'hidden' }}>
      {/* 0.35 Opacity Analog Grain Texture Overlay */}
      <GrainOverlay />

      {/* Floating Glassy Pill-Shaped Navigation Bar */}
      <Navbar currentTab={currentTab} setCurrentTab={setCurrentTab} />

      {/* Main Centered Application Content */}
      <main
        style={{
          flex: 1,
          paddingTop: '88px',
          paddingBottom: '48px',
          position: 'relative',
          zIndex: 1,
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxSizing: 'border-box',
        }}
      >
        {currentTab === 'home' && (
          <Home
            onNavigateToLogin={() => setCurrentTab('login')}
            onNavigateToBook={handleNavigateToBook}
          />
        )}

        {currentTab === 'login' && (
          <Login onLoginSuccess={handleLoginSuccess} />
        )}

        {currentTab === 'patient' && (
          user?.role === 'patient' ? (
            <PatientDashboard />
          ) : (
            <Login onLoginSuccess={handleLoginSuccess} />
          )
        )}

        {currentTab === 'doctor' && (
          user?.role === 'doctor' ? (
            <DoctorDashboard />
          ) : (
            <Login onLoginSuccess={handleLoginSuccess} />
          )
        )}

        {currentTab === 'staff' && (
          ['staff', 'admin', 'sub_admin'].includes(user?.role) ? (
            <StaffDashboard />
          ) : (
            <Login onLoginSuccess={handleLoginSuccess} />
          )
        )}
      </main>

      {/* Glassy Minimalist Footer */}
      <footer
        style={{
          width: '100%',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderTop: '1px solid var(--line)',
          padding: '28px 20px',
          textAlign: 'center',
          color: 'var(--muted)',
          fontSize: '0.9rem',
          position: 'relative',
          zIndex: 1,
          boxSizing: 'border-box',
        }}
      >
        <div className="container" style={{ padding: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
            <NetraCareLogo size={24} />
            <span style={{ fontWeight: 600, color: 'var(--ink)' }}>NetraCare AI Front Desk & Care Coordination</span>
            <span>·</span>
            <span className="cursive" style={{ fontSize: '18px', color: 'var(--muted)' }}>gentle clinical precision</span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
            Asia/Kolkata Timezone · Zero Double Bookings Guarantee · Deterministic Emergency Red-Flag Triage
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
