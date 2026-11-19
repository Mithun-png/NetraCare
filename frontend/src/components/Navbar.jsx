import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Stethoscope, ShieldCheck, Menu, X } from 'lucide-react';
import NetraCareLogo from './NetraCareLogo';

export default function Navbar({ currentTab, setCurrentTab }) {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNav = (tab, scrollId = null) => {
    setMobileMenuOpen(false);
    setCurrentTab(tab);
    if (scrollId && tab === 'home') {
      setTimeout(() => {
        const el = document.getElementById(scrollId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 60);
    }
  };

  return (
    <header className="nav-pill-wrapper">
      <nav className="nav-pill-bar" aria-label="NetraCare Navigation">
        {/* Brand & New NetraCare Ophthalmic Logo */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
          onClick={() => handleNav('home')}
        >
          <NetraCareLogo size={36} />

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span
              style={{
                fontSize: '1.25rem',
                fontWeight: 600,
                color: 'var(--ink)',
                letterSpacing: '-0.025em',
                fontFamily: 'var(--font-display)',
              }}
            >
              NetraCare
            </span>
            <span
              className="cursive"
              style={{
                fontSize: '18px',
                color: 'var(--muted)',
                transform: 'rotate(-2deg)',
              }}
            >
              eye clinic
            </span>
          </div>
        </div>

        {/* Desktop Links (Glassy Pill Buttons) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }} className="hide-on-mobile">
          <button
            className={`nav-link-btn ${currentTab === 'home' ? 'active' : ''}`}
            onClick={() => handleNav('home')}
          >
            Clinic Info
          </button>

          <button
            className="nav-link-btn"
            onClick={() => handleNav('home', 'doctors')}
          >
            Doctors
          </button>

          <button
            className="nav-link-btn"
            onClick={() => handleNav('home', 'schedule')}
          >
            OPD Grid
          </button>

          <button
            className="nav-link-btn"
            onClick={() => handleNav('home', 'faq')}
          >
            FAQ
          </button>

          {user?.role === 'patient' && (
            <button
              className={`nav-link-btn ${currentTab === 'patient' ? 'active' : ''}`}
              onClick={() => handleNav('patient')}
            >
              My Appointments
            </button>
          )}

          {user?.role === 'doctor' && (
            <button
              className={`nav-link-btn ${currentTab === 'doctor' ? 'active' : ''}`}
              onClick={() => handleNav('doctor')}
            >
              Doctor Schedule
            </button>
          )}

          {['staff', 'admin', 'sub_admin'].includes(user?.role) && (
            <button
              className={`nav-link-btn ${currentTab === 'staff' ? 'active' : ''}`}
              onClick={() => handleNav('staff')}
            >
              Staff Dashboard
            </button>
          )}
        </div>

        {/* Right Action: Dark Stone #292524 CTA Button or Authenticated User Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-opd" style={{ textTransform: 'capitalize' }}>
                {user.role === 'patient' && <User size={13} style={{ marginRight: '4px' }} />}
                {user.role === 'doctor' && <Stethoscope size={13} style={{ marginRight: '4px' }} />}
                {['staff', 'admin', 'sub_admin'].includes(user.role) && <ShieldCheck size={13} style={{ marginRight: '4px' }} />}
                {user.name.split(' ')[0]} ({user.role})
              </span>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.82rem' }}
                onClick={() => {
                  logout();
                  setCurrentTab('home');
                }}
              >
                <LogOut size={13} /> Log out
              </button>
            </div>
          ) : (
            <button
              className="btn btn-dark"
              style={{
                padding: '9px 20px',
                fontSize: '14px',
                fontWeight: 500,
              }}
              onClick={() => setCurrentTab('login')}
            >
              Access Portals
            </button>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              background: 'rgba(255, 255, 255, 0.7)',
              border: '1px solid var(--line)',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              cursor: 'pointer',
              color: 'var(--ink)',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            className="mobile-nav-toggle"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer Menu with Liquid Glass Styling */}
      {mobileMenuOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            width: 'calc(100% - 32px)',
            maxWidth: '480px',
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.94) 0%, rgba(253, 252, 248, 0.90) 100%)',
            backdropFilter: 'blur(28px) saturate(180%)',
            WebkitBackdropFilter: 'blur(28px) saturate(180%)',
            borderRadius: '24px',
            border: '1px solid rgba(255, 255, 255, 0.95)',
            outline: '1px solid rgba(231, 229, 228, 0.6)',
            padding: '20px',
            boxShadow: '0 20px 48px -8px rgba(41, 37, 36, 0.12)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            zIndex: 110,
            pointerEvents: 'auto',
          }}
        >
          <button
            className="btn btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
            onClick={() => handleNav('home')}
          >
            Clinic Info
          </button>
          <button
            className="btn btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
            onClick={() => handleNav('home', 'doctors')}
          >
            Our Specialists
          </button>
          <button
            className="btn btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
            onClick={() => handleNav('home', 'schedule')}
          >
            Weekly OPD Grid
          </button>
          <button
            className="btn btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
            onClick={() => handleNav('home', 'faq')}
          >
            FAQ
          </button>

          {user?.role === 'patient' && (
            <button
              className="btn btn-primary"
              style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
              onClick={() => handleNav('patient')}
            >
              My Appointments
            </button>
          )}

          {user?.role === 'doctor' && (
            <button
              className="btn btn-primary"
              style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
              onClick={() => handleNav('doctor')}
            >
              Doctor Schedule
            </button>
          )}

          {['staff', 'admin', 'sub_admin'].includes(user?.role) && (
            <button
              className="btn btn-primary"
              style={{ justifyContent: 'flex-start', padding: '12px 18px', fontSize: '15px' }}
              onClick={() => handleNav('staff')}
            >
              Staff Dashboard
            </button>
          )}
        </div>
      )}
    </header>
  );
}
