import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Clock, Calendar, AlertTriangle, ShieldCheck, ChevronRight } from 'lucide-react';

export default function Home({ onNavigateToLogin, onNavigateToBook }) {
  const [clinic, setClinic] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [holidays, setHolidays] = useState([]);

  useEffect(() => {
    api.getClinicInfo().then(setClinic).catch(console.error);
    api.getDoctors().then(setDoctors).catch(console.error);
    api.getHolidays().then(setHolidays).catch(console.error);
  }, []);

  return (
    <div className="container" style={{ display: 'grid', gap: '32px' }}>
      {/* Hero */}
      <section style={{
        background: 'linear-gradient(135deg, var(--accent-soft) 0%, #ffffff 100%)',
        border: '1px solid var(--line)',
        borderRadius: '16px',
        padding: '36px 32px',
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1fr) auto',
        gap: '24px',
        alignItems: 'center',
      }}>
        <div>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            color: 'var(--accent)',
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>
            AI Front Desk & Care Coordination
          </span>
          <h2 style={{ fontSize: '2.4rem', marginTop: '8px', marginBottom: '12px' }}>
            NetraCare Eye Clinic
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.1rem', maxWidth: '580px', marginBottom: '20px' }}>
            Expert ophthalmic care across 5 superspecialists. Zero double-booking, guaranteed emergency triage, and seamless appointment coordination.
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" onClick={onNavigateToBook}>
              Book Appointment <ChevronRight size={16} />
            </button>
            <button className="btn btn-secondary" onClick={onNavigateToLogin}>
              Access Portals
            </button>
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          border: '1px solid var(--line)',
          borderRadius: '12px',
          padding: '20px 24px',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.04)',
        }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--accent)' }}>N</div>
          <div style={{ fontSize: '1.5rem', letterSpacing: '0.15em', fontWeight: 700 }}>E T</div>
          <div style={{ fontSize: '1rem', letterSpacing: '0.25em', fontWeight: 600 }}>R A C</div>
          <div style={{ fontSize: '0.75rem', letterSpacing: '0.35em', color: 'var(--muted)' }}>A R E</div>
          <p style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: '8px' }}>CLINIC VISION TEST</p>
        </div>
      </section>

      {/* Clinic Hours & Schedule */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Clock size={20} color="var(--accent)" />
            <h3>Timings & Sessions</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'grid', gap: '8px', fontSize: '0.95rem' }}>
            <li><b>Operating Days:</b> Monday to Saturday</li>
            <li><b>Morning Session:</b> 09:00 AM – 01:00 PM</li>
            <li><b>Lunch Break:</b> 01:00 PM – 02:00 PM (Closed)</li>
            <li><b>Evening Session:</b> 02:00 PM – 06:00 PM</li>
            <li style={{ color: 'var(--danger)', fontWeight: 600 }}>Closed on Sundays and Listed Holidays</li>
          </ul>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <ShieldCheck size={20} color="var(--accent)" />
            <h3>Clinic Rules Enforced</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'grid', gap: '8px', fontSize: '0.95rem' }}>
            <li>✓ <b>New Consultation:</b> 20 minutes</li>
            <li>✓ <b>Follow-up Visit:</b> 10 minutes (with previous doctor)</li>
            <li>✓ <b>Booking Window:</b> Up to 30 days ahead</li>
            <li>✓ <b>Cancellation Window:</b> Up to 2 hours before start</li>
            <li>✓ <b>Safety Rule:</b> Immediate triage for red-flag symptoms</li>
          </ul>
        </div>
      </div>

      {/* Doctors & Specialities */}
      <section className="card">
        <h3 style={{ fontSize: '1.4rem', marginBottom: '16px' }}>Our Doctors & Specialities</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {doctors.map((doc) => (
            <div key={doc.id} style={{
              border: '1px solid var(--line)',
              borderRadius: '10px',
              padding: '16px',
              background: '#fff',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="mono" style={{ fontWeight: 600, color: 'var(--accent)' }}>{doc.id}</span>
                <span className="badge badge-opd">Active</span>
              </div>
              <h4 style={{ fontSize: '1.1rem', marginBottom: '6px' }}>{doc.name}</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                {doc.specialities.map((spec) => (
                  <span key={spec} style={{
                    fontSize: '0.8rem',
                    background: 'var(--bg)',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--line)',
                  }}>
                    {spec}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Weekly OPD Schedule Grid */}
      <section className="card">
        <h3 style={{ fontSize: '1.4rem', marginBottom: '14px' }}>Weekly OPD Grid</h3>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem', marginBottom: '16px' }}>
          Doctors conduct Outpatient Consultations (OPD), Surgeries (SX), or have scheduled off days.
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
            <thead>
              <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--line)' }}>
                <th style={{ padding: '10px', textAlign: 'left' }}>Doctor</th>
                <th style={{ padding: '10px' }}>Mon</th>
                <th style={{ padding: '10px' }}>Tue</th>
                <th style={{ padding: '10px' }}>Wed</th>
                <th style={{ padding: '10px' }}>Thu</th>
                <th style={{ padding: '10px' }}>Fri</th>
                <th style={{ padding: '10px' }}>Sat</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Dr. Anand Rao</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr>
                <td style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Dr. Meera Iyer</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr>
                <td style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Dr. Kiran Shah</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
              </tr>
              <tr>
                <td style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Dr. Fatima Khan</td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr>
                <td style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Dr. Vikram Menon</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

