import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import FactOfTheDay from '../components/FactOfTheDay';
import { Calendar, Clock, AlertTriangle, CheckCircle, XCircle, RefreshCw, UserCheck } from 'lucide-react';

export default function PatientDashboard() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);

  // Booking form state
  const [doctorId, setDoctorId] = useState('D1');
  const [speciality, setSpeciality] = useState('Cataract');
  const [visitType, setVisitType] = useState('new');
  const [date, setDate] = useState(() => {
    // Tomorrow as sensible default
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [reason, setReason] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [emergencyAlert, setEmergencyAlert] = useState(null);

  // Load appointments and doctors
  const refreshAppointments = async () => {
    try {
      const data = await api.getMyAppointments();
      setAppointments(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    api.getDoctors().then((docs) => {
      setDoctors(docs);
      if (docs.length > 0) {
        setDoctorId(docs[0].id);
        setSpeciality(docs[0].specialities[0]);
      }
    });
    refreshAppointments().finally(() => setLoading(false));
  }, []);

  // Update available specialities when doctor changes
  const handleDoctorChange = (docId) => {
    setDoctorId(docId);
    const doc = doctors.find((d) => d.id === docId);
    if (doc && doc.specialities.length > 0) {
      setSpeciality(doc.specialities[0]);
    }
    setSelectedSlot('');
  };

  // Fetch free slots whenever doctor, date, or visitType changes
  useEffect(() => {
    if (!doctorId || !date) return;
    setSelectedSlot('');
    api.getSlots(doctorId, date, visitType)
      .then((res) => {
        setSlots(res.slots || []);
      })
      .catch((err) => {
        setSlots([]);
      });
  }, [doctorId, date, visitType]);

  const handleBookSubmit = async (e) => {
    e.preventDefault();
    setBookingError(null);
    setBookingSuccess(null);
    setEmergencyAlert(null);

    if (!selectedSlot) {
      setBookingError('Please select an available time slot.');
      return;
    }

    setBookingLoading(true);
    try {
      const res = await api.bookAppointment({
        doctor_id: doctorId,
        speciality,
        visit_type: visitType,
        date,
        start_time: selectedSlot,
        reason: reason.trim() || undefined,
      });

      if (res.ok) {
        setBookingSuccess('Appointment booked successfully!');
        setReason('');
        setSelectedSlot('');
        refreshAppointments();
      }
    } catch (err) {
      if (err.data?.reason_code === 'RED_FLAG') {
        setEmergencyAlert(err.data.message);
      } else {
        setBookingError(err.data?.message || err.message || 'Booking refused by clinic rules.');
      }
    } finally {
      setBookingLoading(false);
    }
  };

  const handleCancel = async (apptId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      const res = await api.cancelMyAppointment(apptId, 'Patient requested cancellation');
      if (res.ok) {
        alert('Appointment cancelled successfully.');
      } else if (res.expected === 'to_staff') {
        alert('This appointment starts in under 2 hours. Your cancellation request has been forwarded to clinic staff for approval.');
      }
      refreshAppointments();
    } catch (err) {
      alert(err.message || 'Could not cancel appointment.');
    }
  };

  return (
    <div className="container" style={{ display: 'grid', gap: '28px' }}>
      <div>
        <h2 style={{ fontSize: '2rem' }}>Welcome, {user.name}</h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
          Patient ID: <span className="mono">{user.id}</span> · Book, manage, or cancel your consultations.
        </p>
      </div>

      {/* Fact of the Day (Iteration 2 R5) */}
      <FactOfTheDay />

      {emergencyAlert && (
        <div className="banner-urgent">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <AlertTriangle size={24} />
            <h3 style={{ color: 'var(--danger)', margin: 0 }}>URGENT MEDICAL ATTENTION REQUIRED</h3>
          </div>
          <p style={{ fontSize: '1.05rem', fontWeight: 600 }}>{emergencyAlert}</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Booking Wizard Card */}
        <div className="card">
          <h3 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Book an Appointment</h3>

          {bookingSuccess && (
            <div style={{
              background: 'var(--success-soft)',
              border: '1px solid var(--success)',
              color: 'var(--success)',
              padding: '10px 14px',
              borderRadius: '8px',
              marginBottom: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <CheckCircle size={18} />
              <span>{bookingSuccess}</span>
            </div>
          )}

          {bookingError && (
            <div style={{
              background: 'var(--danger-soft)',
              border: '1px solid var(--danger)',
              color: 'var(--danger)',
              padding: '10px 14px',
              borderRadius: '8px',
              marginBottom: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <XCircle size={18} />
              <span>{bookingError}</span>
            </div>
          )}

          <form onSubmit={handleBookSubmit}>
            <div className="form-group">
              <label className="form-label">Doctor</label>
              <select
                className="form-control"
                value={doctorId}
                onChange={(e) => handleDoctorChange(e.target.value)}
              >
                {doctors.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.id})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Speciality</label>
              <select
                className="form-control"
                value={speciality}
                onChange={(e) => setSpeciality(e.target.value)}
              >
                {doctors.find((d) => d.id === doctorId)?.specialities.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Visit Type</label>
              <select
                className="form-control"
                value={visitType}
                onChange={(e) => setVisitType(e.target.value)}
              >
                <option value="new">New Consultation (20 mins)</option>
                <option value="follow_up">Follow-up Visit (10 mins)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Date</label>
              <input
                type="date"
                className="form-control"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Available Slots</label>
              {slots.length === 0 ? (
                <div style={{
                  padding: '12px',
                  background: 'var(--bg)',
                  borderRadius: '8px',
                  color: 'var(--muted)',
                  fontSize: '0.88rem',
                  textAlign: 'center',
                }}>
                  No available slots on this date (Closed, Surgery, Off, or Fully Booked).
                </div>
              ) : (
                <div className="slot-grid">
                  {slots.map((s) => (
                    <button
                      type="button"
                      key={s.start_time}
                      className={`slot-btn ${selectedSlot === s.start_time ? 'selected' : ''}`}
                      onClick={() => setSelectedSlot(s.start_time)}
                    >
                      {s.start_time}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">
                  Reason for Visit <span style={{ color: 'var(--danger)' }}>*</span>
                </label>
                <span style={{ fontSize: '0.78rem', color: reason.length > 300 ? 'var(--danger)' : 'var(--muted)' }}>
                  {reason.length}/300
                </span>
              </div>
              <textarea
                className="form-control"
                rows="2"
                placeholder="What is the reason for your visit? Describe your symptoms..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                maxLength={300}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '6px' }}
              disabled={bookingLoading || !selectedSlot}
            >
              {bookingLoading ? 'Checking Rules & Booking...' : `Confirm Booking (${selectedSlot || 'Select Slot'})`}
            </button>
          </form>
        </div>

        {/* My Appointments List */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.3rem' }}>My Consultation History</h3>
            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={refreshAppointments}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {loading ? (
            <p style={{ color: 'var(--muted)' }}>Loading appointments...</p>
          ) : appointments.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No appointments found. Book your first consultation on the left.</p>
          ) : (
            <div style={{ display: 'grid', gap: '12px' }}>
              {appointments.map((a) => (
                <div
                  key={a.id}
                  style={{
                    border: '1px solid var(--line)',
                    borderRadius: '10px',
                    padding: '16px',
                    background: a.status === 'booked' ? '#ffffff' : 'var(--bg)',
                    display: 'grid',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span className="mono" style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{a.id}</span>
                      <h4 style={{ fontSize: '1.1rem', marginTop: '2px' }}>{a.doctor_name}</h4>
                      <p style={{ fontSize: '0.88rem', color: 'var(--accent)', fontWeight: 600 }}>
                        {a.speciality} · {a.visit_type === 'new' ? 'New Visit (20m)' : 'Follow-up (10m)'}
                      </p>
                    </div>
                    <span className={`badge badge-${a.status}`}>
                      {a.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.9rem', color: 'var(--muted)' }}>
                    <span>📅 {a.date}</span>
                    <span>⏰ {a.start_time} – {a.end_time}</span>
                  </div>

                  {a.reason && (
                    <p style={{ fontSize: '0.88rem', color: 'var(--ink)' }}>
                      <b>Reported symptoms:</b> {a.reason}
                    </p>
                  )}

                  {a.doctor_note && (
                    <div style={{
                      background: 'var(--accent-soft)',
                      borderLeft: '3px solid var(--accent)',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                    }}>
                      <b>Doctor's Clinical Notes:</b> {a.doctor_note}
                    </div>
                  )}

                  {a.status === 'booked' && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                      <button
                        className="btn btn-danger"
                        style={{ padding: '4px 10px', fontSize: '0.85rem' }}
                        onClick={() => handleCancel(a.id)}
                      >
                        Cancel Appointment
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

