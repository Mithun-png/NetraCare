import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar currentTab={currentTab} setCurrentTab={setCurrentTab} />

      <main style={{ flex: 1, paddingBottom: '48px' }}>
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

      <footer style={{
        background: '#fff',
        borderTop: '1px solid var(--line)',
        padding: '20px 0',
        textAlign: 'center',
        color: 'var(--muted)',
        fontSize: '0.85rem',
      }}>
        <div className="container">
          <p>NetraCare AI Front Desk & Care Coordination · Fictional Clinic Capstone · All Data Synthetic</p>
          <p style={{ marginTop: '4px' }}>Asia/Kolkata Timezone · Zero Double Bookings Guarantee · Deterministic Red-Flag Triage</p>
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

