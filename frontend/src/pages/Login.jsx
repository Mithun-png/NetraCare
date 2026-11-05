import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Stethoscope, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react';

const DEMO_PATIENTS = [
  { id: 'P01', name: 'Asha Verma', mobile: '9000000001', note: 'Cataract & Retina history' },
  { id: 'P02', name: 'Rohan Gupta', mobile: '9000000002', note: 'General eye health' },
  { id: 'P03', name: 'Lakshmi Nair', mobile: '9000000003', note: 'Glaucoma history' },
  { id: 'P04', name: 'Imran Sheikh', mobile: '9000000004', note: 'Dry eye care' },
  { id: 'P13', name: 'Fatima Begum', mobile: '9000000013', note: 'Retina history' },
  { id: 'P18', name: 'Harish Chandra', mobile: '9000000018', note: 'Cataract follow-up' },
];

const DOCTORS = [
  { id: 'D1', name: 'Dr. Anand Rao', spec: 'Cataract, General' },
  { id: 'D2', name: 'Dr. Meera Iyer', spec: 'Glaucoma, Cataract' },
  { id: 'D3', name: 'Dr. Kiran Shah', spec: 'Retina, General' },
  { id: 'D4', name: 'Dr. Fatima Khan', spec: 'Cornea, Refractive, Dry eye' },
  { id: 'D5', name: 'Dr. Vikram Menon', spec: 'Paediatric, Squint, General' },
];

export default function Login({ onLoginSuccess }) {
  const { login } = useAuth();
  const [role, setRole] = useState('patient');
  const [mobile, setMobile] = useState('');
  const [name, setName] = useState('');
  const [doctorId, setDoctorId] = useState('D1');
  const [staffName, setStaffName] = useState('Front Desk Staff');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      let payload;
      if (role === 'patient') {
        payload = { role: 'patient', mobile: mobile.trim(), name: name.trim() };
      } else if (role === 'doctor') {
        payload = { role: 'doctor', doctor_id: doctorId };
      } else {
        payload = { role: 'staff', name: staffName.trim() };
      }

      const res = await login(payload);
      if (res.ok) {
        onLoginSuccess(role);
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your details.');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePickDemoPatient = (p) => {
    setMobile(p.mobile);
    setName(p.name);
    setError(null);
  };

  return (
    <div className="container" style={{ maxWidth: '560px', marginTop: '24px' }}>
      <div className="card" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '8px' }}>Sign In to NetraCare</h2>
        <p style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '0.95rem', marginBottom: '24px' }}>
          Select your portal role to access your schedule and care appointments.
        </p>

        {/* Role Tabs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '8px',
          background: 'var(--bg)',
          padding: '6px',
          borderRadius: '10px',
          marginBottom: '24px',
        }}>
          <button
            type="button"
            className="btn"
            style={{
              background: role === 'patient' ? '#fff' : 'transparent',
              color: role === 'patient' ? 'var(--accent)' : 'var(--muted)',
              border: role === 'patient' ? '1px solid var(--line)' : 'none',
              boxShadow: role === 'patient' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
            }}
            onClick={() => { setRole('patient'); setError(null); }}
          >
            <User size={16} /> Patient
          </button>
          <button
            type="button"
            className="btn"
            style={{
              background: role === 'doctor' ? '#fff' : 'transparent',
              color: role === 'doctor' ? 'var(--accent)' : 'var(--muted)',
              border: role === 'doctor' ? '1px solid var(--line)' : 'none',
              boxShadow: role === 'doctor' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
            }}
            onClick={() => { setRole('doctor'); setError(null); }}
          >
            <Stethoscope size={16} /> Doctor
          </button>
          <button
            type="button"
            className="btn"
            style={{
              background: role === 'staff' ? '#fff' : 'transparent',
              color: role === 'staff' ? 'var(--accent)' : 'var(--muted)',
              border: role === 'staff' ? '1px solid var(--line)' : 'none',
              boxShadow: role === 'staff' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
            }}
            onClick={() => { setRole('staff'); setError(null); }}
          >
            <ShieldCheck size={16} /> Staff
          </button>
        </div>

        {error && (
          <div style={{
            background: 'var(--danger-soft)',
            border: '1px solid var(--danger)',
            color: 'var(--danger)',
            borderRadius: '8px',
            padding: '12px 14px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.9rem',
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {role === 'patient' && (
            <div>
              <div className="form-group">
                <label className="form-label">Mobile Number</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. 9000000001"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Asha Verma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              {/* Demo Patient Fast Picker */}
              <div style={{ marginTop: '14px', marginBottom: '20px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Quick pick demo patient:</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                  {DEMO_PATIENTS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handlePickDemoPatient(p)}
                      style={{
                        fontSize: '0.8rem',
                        border: '1px solid var(--line)',
                        background: mobile === p.mobile ? 'var(--accent-soft)' : 'var(--bg)',
                        color: mobile === p.mobile ? 'var(--accent)' : 'var(--ink)',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                      }}
                    >
                      {p.name} ({p.id})
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {role === 'doctor' && (
            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label">Select Your Doctor Profile</label>
              <select
                className="form-control"
                value={doctorId}
                onChange={(e) => setDoctorId(e.target.value)}
              >
                {DOCTORS.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.id}) — {d.spec}
                  </option>
                ))}
              </select>
            </div>
          )}

          {role === 'staff' && (
            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label">Staff Member Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="Front Desk Staff"
                value={staffName}
                onChange={(e) => setStaffName(e.target.value)}
                required
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px' }}
            disabled={submitting}
          >
            {submitting ? 'Authenticating...' : 'Sign In'} <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

