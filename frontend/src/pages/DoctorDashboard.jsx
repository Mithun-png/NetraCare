import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Calendar, Clock, CheckCircle2, FileText, User, Sparkles, AlertCircle } from 'lucide-react';

export default function DoctorDashboard() {
  const { user } = useAuth();
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Complete visit modal state
  const [activeAppt, setActiveAppt] = useState(null);
  const [clinicalNote, setClinicalNote] = useState('');
  const [completing, setCompleting] = useState(false);

  // Patient summary modal state (Iteration 2 R6)
  const [summaryData, setSummaryData] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);

  // Leave modal state (Iteration 4 R7)
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveDate, setLeaveDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [leaveSession, setLeaveSession] = useState('FULL');
  const [leaveSubmitting, setLeaveSubmitting] = useState(false);

  const fetchSchedule = async (selectedDate) => {
    setLoading(true);
    try {
      const res = await api.getDoctorSchedule(selectedDate);
      setScheduleData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule(date);
  }, [date]);

  const handleOpenSummary = async (apptId) => {
    setSummaryLoading(true);
    setSummaryError(null);
    setSummaryData(null);
    try {
      const res = await api.getDoctorPatientSummary(apptId);
      setSummaryData(res);
    } catch (e) {
      setSummaryError(e.message || 'Failed to load summary.');
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleCompleteSubmit = async (e) => {
    e.preventDefault();
    if (!clinicalNote.trim()) {
      alert('Please enter clinical findings and advice.');
      return;
    }
    setCompleting(true);
    try {
      await api.completeVisit(activeAppt.id, clinicalNote.trim());
      alert(`Visit ${activeAppt.id} successfully marked as completed.`);
      setActiveAppt(null);
      setClinicalNote('');
      fetchSchedule(date);
    } catch (err) {
      alert(err.message || 'Failed to complete visit.');
    } finally {
      setCompleting(false);
    }
  };

  const handleLeaveSubmit = async (e) => {
    e.preventDefault();
    setLeaveSubmitting(true);
    try {
      const res = await api.markDoctorLeave({ date: leaveDate, session: leaveSession });
      alert(`Leave recorded! ${res.affected_count} affected appointments moved to proposals for Staff.`);
      setShowLeaveModal(false);
      fetchSchedule(date);
    } catch (err) {
      alert(err.message || 'Failed to record leave.');
    } finally {
      setLeaveSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ display: 'grid', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.9rem' }}>{user.name} — OPD Schedule</h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>Doctor ID: <span className="mono">{user.id}</span></p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={() => setShowLeaveModal(true)} style={{ color: 'var(--accent)' }}>
            Mark Leave (R7)
          </button>
          <label style={{ fontWeight: 600, fontSize: '0.9rem' }}>Select Date:</label>
          <input
            type="date"
            className="form-control"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={{ width: '180px' }}
          />
        </div>
      </div>

      {/* Session status banner */}
      {scheduleData?.sessions && (
        <div className="card" style={{ display: 'flex', gap: '24px', alignItems: 'center', padding: '14px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 600 }}>Morning Session (09:00 - 13:00):</span>
            <span className={`badge badge-${scheduleData.sessions.AM?.toLowerCase()}`}>
              {scheduleData.sessions.AM || 'NO OPD'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 600 }}>Evening Session (14:00 - 18:00):</span>
            <span className={`badge badge-${scheduleData.sessions.PM?.toLowerCase()}`}>
              {scheduleData.sessions.PM || 'NO OPD'}
            </span>
          </div>
        </div>
      )}

      {/* Appointment table */}
      <div className="card">
        <h3 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>
          Consultation Roster for {date} ({scheduleData?.appointments?.length || 0} scheduled)
        </h3>

        {loading ? (
          <p style={{ color: 'var(--muted)' }}>Loading schedule...</p>
        ) : scheduleData?.appointments?.length === 0 ? (
          <p style={{ color: 'var(--muted)' }}>No appointments scheduled for this day.</p>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {scheduleData?.appointments?.map((a) => (
              <div
                key={a.id}
                style={{
                  border: '1px solid var(--line)',
                  borderRadius: '10px',
                  padding: '16px 20px',
                  display: 'grid',
                  gridTemplateColumns: '120px 1fr auto',
                  gap: '16px',
                  alignItems: 'center',
                  background: a.status === 'completed' ? 'var(--bg)' : '#fff',
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', fontFamily: 'var(--font-mono)' }}>
                    {a.start_time}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                    to {a.end_time}
                  </div>
                  <span className={`badge badge-${a.status}`} style={{ marginTop: '4px' }}>
                    {a.status}
                  </span>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{a.patient_name}</span>
                    <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>({a.patient_id})</span>
                    <span style={{
                      fontSize: '0.8rem',
                      background: 'var(--accent-soft)',
                      color: 'var(--accent)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 600,
                    }}>
                      {a.speciality} · {a.visit_type}
                    </span>
                  </div>

                  {a.reason && (
                    <p style={{ fontSize: '0.88rem', color: 'var(--ink)', marginTop: '4px' }}>
                      <b>Intake Symptoms:</b> {a.reason}
                    </p>
                  )}

                  {a.intake_notes && (
                    <div style={{
                      marginTop: '8px',
                      padding: '8px 12px',
                      background: 'var(--accent-soft)',
                      borderRadius: '6px',
                      fontSize: '0.85rem',
                      whiteSpace: 'pre-wrap',
                    }}>
                      <b>Pre-Assessment Intake Notes:</b>
                      <div style={{ marginTop: '4px' }}>{a.intake_notes}</div>
                    </div>
                  )}

                  {a.doctor_note && (
                    <p style={{ fontSize: '0.88rem', color: 'var(--success)', marginTop: '4px' }}>
                      <b>Clinical Note:</b> {a.doctor_note}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleOpenSummary(a.id)}
                  >
                    <Sparkles size={14} color="var(--accent)" /> AI Summary & History
                  </button>

                  {a.status === 'booked' && (
                    <button
                      className="btn btn-primary"
                      style={{ padding: '6px 14px', fontSize: '0.85rem' }}
                      onClick={() => {
                        setActiveAppt(a);
                        setClinicalNote(a.doctor_note || '');
                      }}
                    >
                      <CheckCircle2 size={16} /> Complete Visit
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Complete Visit Modal */}
      {activeAppt && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '16px',
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '28px' }}>
            <h3 style={{ fontSize: '1.4rem', marginBottom: '8px' }}>Complete Patient Visit</h3>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
              Patient: <b>{activeAppt.patient_name}</b> ({activeAppt.speciality}) · {activeAppt.start_time}
            </p>

            <form onSubmit={handleCompleteSubmit}>
              <div className="form-group">
                <label className="form-label">Doctor's Clinical Notes & Follow-up Guidance:</label>
                <textarea
                  className="form-control"
                  rows="4"
                  placeholder="Record diagnosis, visual acuity findings, prescription, and review timeline (e.g. 'VA 6/9 OD, IOP 16 mmHg. Advised review in 6 months')..."
                  value={clinicalNote}
                  onChange={(e) => setClinicalNote(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setActiveAppt(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={completing}
                >
                  {completing ? 'Saving...' : 'Finalize & Mark Completed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Patient AI Summary & Past Notes Modal (Iteration 2 R6) */}
      {(summaryLoading || summaryData || summaryError) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '16px',
        }}>
          <div className="card" style={{ maxWidth: '640px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={20} color="var(--accent)" />
                <h3 style={{ fontSize: '1.3rem', margin: 0 }}>Clinical Patient Intake Summary</h3>
              </div>
              <button
                className="btn btn-secondary"
                style={{ padding: '4px 8px', fontSize: '0.85rem' }}
                onClick={() => {
                  setSummaryData(null);
                  setSummaryError(null);
                  setSummaryLoading(false);
                }}
              >
                ✕ Close
              </button>
            </div>

            {summaryLoading && (
              <p style={{ color: 'var(--muted)', padding: '24px 0', textAlign: 'center' }}>
                Analyzing clinical history with LLM...
              </p>
            )}

            {summaryError && (
              <div style={{
                background: 'var(--danger-soft)',
                border: '1px solid var(--danger)',
                color: 'var(--danger)',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '16px',
              }}>
                {summaryError}
              </div>
            )}

            {summaryData && (
              <div style={{ display: 'grid', gap: '16px' }}>
                {/* Patient Profile Header */}
                <div style={{ background: 'var(--bg)', padding: '12px 16px', borderRadius: '8px', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                    <span>{summaryData.patient_name} ({summaryData.patient_id})</span>
                    <span>Age: {summaryData.age || 'N/A'}</span>
                  </div>
                  <div style={{ color: 'var(--muted)', marginTop: '4px' }}>
                    <b>General Health:</b> {summaryData.general_health || 'None recorded'} · <b>Allergies:</b> {summaryData.allergies || 'None known'}
                  </div>
                  <div style={{ color: 'var(--ink)', marginTop: '4px' }}>
                    <b>Today's Stated Reason:</b> {summaryData.todays_reason || 'Routine consultation'}
                  </div>
                </div>

                {/* AI Summary Box */}
                <div style={{
                  background: 'var(--accent-soft)',
                  border: '1px solid var(--accent)',
                  borderRadius: '10px',
                  padding: '16px',
                }}>
                  <div style={{
                    fontSize: '0.78rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: 'var(--accent)',
                    marginBottom: '6px',
                  }}>
                    {summaryData.label}
                  </div>
                  <p style={{ fontSize: '0.96rem', color: 'var(--ink)', lineHeight: 1.5 }}>
                    {summaryData.summary}
                  </p>
                </div>

                {/* Full Past Clinical Notes Section */}
                <div>
                  <h4 style={{ fontSize: '1.05rem', marginBottom: '10px' }}>
                    Full Recorded Past Notes ({summaryData.past_notes?.length || 0})
                  </h4>
                  {summaryData.past_notes?.length === 0 ? (
                    <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>No previous consultations on record.</p>
                  ) : (
                    <div style={{ display: 'grid', gap: '10px' }}>
                      {summaryData.past_notes.map((note) => (
                        <div
                          key={note.id}
                          style={{
                            border: '1px solid var(--line)',
                            borderRadius: '8px',
                            padding: '12px',
                            background: '#ffffff',
                            fontSize: '0.88rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', marginBottom: '4px' }}>
                            <span style={{ fontWeight: 600, color: 'var(--accent)' }}>
                              {note.doctor_name} ({note.speciality})
                            </span>
                            <span>{note.date}</span>
                          </div>
                          {note.reason && (
                            <p style={{ color: 'var(--muted)', marginBottom: '4px' }}>
                              <b>Reason:</b> {note.reason}
                            </p>
                          )}
                          <p style={{ color: 'var(--ink)' }}>
                            <b>Doctor's Note:</b> {note.doctor_note}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {/* Doctor Leave Modal (R7) */}
      {showLeaveModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div className="card" style={{ maxWidth: '480px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Mark Doctor Leave (R7)</h3>
              <button className="btn btn-secondary" onClick={() => setShowLeaveModal(false)}>✕</button>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--muted)', marginBottom: '16px' }}>
              Marking leave cancels affected bookings and automatically generates rebooking proposals for clinic Staff to approve.
            </p>
            <form onSubmit={handleLeaveSubmit} style={{ display: 'grid', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '6px' }}>Leave Date:</label>
                <input
                  type="date"
                  className="form-control"
                  value={leaveDate}
                  onChange={(e) => setLeaveDate(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '6px' }}>Session:</label>
                <select
                  className="form-control"
                  value={leaveSession}
                  onChange={(e) => setLeaveSession(e.target.value)}
                >
                  <option value="FULL">Full Day (AM & PM)</option>
                  <option value="AM">Morning Session (09:00 - 13:00)</option>
                  <option value="PM">Evening Session (14:00 - 18:00)</option>
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowLeaveModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={leaveSubmitting}>
                  {leaveSubmitting ? 'Recording...' : 'Mark Leave & Propose Rebookings'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

