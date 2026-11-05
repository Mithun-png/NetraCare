import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Eye, LogOut, User, Stethoscope, ShieldCheck } from 'lucide-react';

export default function Navbar({ currentTab, setCurrentTab }) {
  const { user, logout } = useAuth();

  return (
    <header style={{ background: '#fff', borderBottom: '1px solid var(--line)', position: 'sticky', top: 0, zIndex: 100 }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => setCurrentTab('home')}>
          <div style={{
            background: 'var(--accent-soft)',
            color: 'var(--accent)',
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Eye size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', letterSpacing: '-0.02em', color: 'var(--ink)' }}>NetraCare</h1>
            <p style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '-2px' }}>AI Front Desk & Eye Clinic</p>
          </div>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className={`btn ${currentTab === 'home' ? 'btn-secondary' : ''}`}
            style={{ border: 'none', background: currentTab === 'home' ? 'var(--accent-soft)' : 'transparent', color: currentTab === 'home' ? 'var(--accent)' : 'var(--ink)' }}
            onClick={() => setCurrentTab('home')}
          >
            Clinic Info
          </button>

          {user?.role === 'patient' && (
            <button
              className="btn"
              style={{ background: currentTab === 'patient' ? 'var(--accent-soft)' : 'transparent', color: currentTab === 'patient' ? 'var(--accent)' : 'var(--ink)', border: 'none' }}
              onClick={() => setCurrentTab('patient')}
            >
              My Appointments
            </button>
          )}

          {user?.role === 'doctor' && (
            <button
              className="btn"
              style={{ background: currentTab === 'doctor' ? 'var(--accent-soft)' : 'transparent', color: currentTab === 'doctor' ? 'var(--accent)' : 'var(--ink)', border: 'none' }}
              onClick={() => setCurrentTab('doctor')}
            >
              Doctor Schedule
            </button>
          )}

          {['staff', 'admin', 'sub_admin'].includes(user?.role) && (
            <button
              className="btn"
              style={{ background: currentTab === 'staff' ? 'var(--accent-soft)' : 'transparent', color: currentTab === 'staff' ? 'var(--accent)' : 'var(--ink)', border: 'none' }}
              onClick={() => setCurrentTab('staff')}
            >
              Staff Dashboard
            </button>
          )}

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '12px', borderLeft: '1px solid var(--line)', paddingLeft: '12px' }}>
              <span className="badge badge-opd" style={{ textTransform: 'capitalize' }}>
                {user.role === 'patient' && <User size={13} style={{ marginRight: '4px' }} />}
                {user.role === 'doctor' && <Stethoscope size={13} style={{ marginRight: '4px' }} />}
                {['staff', 'admin', 'sub_admin'].includes(user.role) && <ShieldCheck size={13} style={{ marginRight: '4px' }} />}
                {user.name} ({user.role})
              </span>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: '0.85rem' }}
                onClick={() => {
                  logout();
                  setCurrentTab('home');
                }}
              >
                <LogOut size={14} /> Log out
              </button>
            </div>
          ) : (
            <button
              className="btn btn-primary"
              style={{ marginLeft: '8px' }}
              onClick={() => setCurrentTab('login')}
            >
              Log in
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}

