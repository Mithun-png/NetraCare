import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import SearchDebugger from '../components/SearchDebugger';
import { AlertTriangle, Check, X, ShieldAlert, Plus, Search, Filter, RefreshCw } from 'lucide-react';

export default function StaffDashboard() {
  const { user } = useAuth();
  const [urgentCases, setUrgentCases] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [rebookings, setRebookings] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [filterDate, setFilterDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [loading, setLoading] = useState(true);

  // Walk-in modal state
  const [showWalkinModal, setShowWalkinModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [patientsList, setPatientsList] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [walkinDocId, setWalkinDocId] = useState('D1');
  const [walkinSpec, setWalkinSpec] = useState('Cataract');
  const [walkinType, setWalkinType] = useState('new');
  const [walkinDate, setWalkinDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [walkinSlot, setWalkinSlot] = useState('');
  const [walkinSlots, setWalkinSlots] = useState([]);
  const [walkinError, setWalkinError] = useState(null);

  const refreshAll = async () => {
    setLoading(true);
    try {
      const [urgentRes, apprRes, rebookRes, apptsRes, docsRes] = await Promise.all([
        api.getUrgentCases(),
        api.getApprovals(),
        api.getStaffRebookings(),
        api.getStaffAppointments({ date: filterDate, doctor_id: selectedDoctor || undefined }),
        api.getDoctors(),
      ]);
      setUrgentCases(urgentRes);
      setApprovals(apprRes);
      setRebookings(rebookRes);
      setAppointments(apptsRes);
      setDoctors(docsRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, [filterDate, selectedDoctor]);

  // Load slots for walk-in modal
  useEffect(() => {
    if (showWalkinModal && walkinDocId && walkinDate) {
      api.getSlots(walkinDocId, walkinDate, walkinType)
        .then((res) => setWalkinSlots(res.slots || []))
        .catch(() => setWalkinSlots([]));
    }
  }, [showWalkinModal, walkinDocId, walkinDate, walkinType]);

  const handlePatientSearch = async (q) => {
    setSearchQuery(q);
    if (q.length >= 2) {
      const res = await api.searchPatients(q);
      setPatientsList(res);
      if (res.length > 0 && !selectedPatientId) {
        setSelectedPatientId(res[0].id);
      }
    }
  };

  const handleMarkSeen = async (id) => {
    await api.markUrgentSeen(id);
    refreshAll();
  };

  const handleDecideApproval = async (id, decision) => {
    if (decision === 'APPROVED') {
      await api.approveApproval(id);
    } else {
      await api.rejectApproval(id);
    }
    refreshAll();
  };

  const handleApproveRebooking = async (id) => {
    await api.approveRebooking(id);
    refreshAll();
  };

  const handleRejectRebooking = async (id) => {
    await api.rejectRebooking(id);
    refreshAll();
  };

  const handleStaffCancel = async (id) => {
    if (!window.confirm('Cancel this appointment on behalf of patient?')) return;
    try {
      await api.staffCancelAppointment(id, 'Front desk cancellation');
      alert('Appointment cancelled.');
      refreshAll();
    } catch (e) {
      alert(e.message || 'Failed to cancel.');
    }
  };

  const handleWalkinSubmit = async (e) => {
    e.preventDefault();
    setWalkinError(null);
    try {
      await api.staffBookAppointment({
        patient_id: selectedPatientId,
        doctor_id: walkinDocId,
        speciality: walkinSpec,
        visit_type: walkinType,
        date: walkinDate,
        start_time: walkinSlot,
        reason: 'Staff walk-in / on-behalf booking',
      });
      alert('Walk-in booked successfully!');
      setShowWalkinModal(false);
      refreshAll();
    } catch (err) {
      setWalkinError(err.data?.message || err.message || 'Booking refused by clinic rules.');
    }
  };

  return (
    <div className="container" style={{ display: 'grid', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.9rem' }}>Staff Care Coordination Desk</h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>Full clinic roster, urgent safety cases, approvals & walk-ins.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-primary" onClick={() => setShowWalkinModal(true)}>
            <Plus size={16} /> Book Walk-in / On-Behalf
          </button>
          <button className="btn btn-secondary" onClick={refreshAll}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Pinned Urgent Cases Banner */}
      {urgentCases.length > 0 && (
        <div className="banner-urgent" style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={24} color="var(--danger)" />
            <h3 style={{ margin: 0, color: 'var(--danger)' }}>
              URGENT CASES ({urgentCases.length} Requiring Immediate Clinic Action)
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--ink)' }}>
            These patients reported red-flag ocular symptoms. Emergency alert was sent and bookings were safely stopped.
          </p>

          <div style={{ display: 'grid', gap: '8px', marginTop: '6px' }}>
            {urgentCases.map((c) => (
              <div
                key={c.id}
                style={{
                  background: '#ffffff',
                  border: '1px solid var(--danger)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--ink)' }}>{c.patient_name}</span>
                    <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>({c.patient_id || 'Walk-in / Unregistered'})</span>
                    <span className="badge badge-sx">Source: {c.source}</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--danger)', fontWeight: 600, marginTop: '4px' }}>
                    {c.summary}
                  </p>
                </div>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.82rem', padding: '6px 12px' }}
                  onClick={() => handleMarkSeen(c.id)}
                >
                  <Check size={14} /> Mark Handled
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Doctor Leave Rebookings Queue (R7) */}
      {rebookings.length > 0 && (
        <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
            Doctor Leave Rebooking Proposals ({rebookings.length} Pending Approval)
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '12px' }}>
            Automated rebooking proposals generated when doctors mark leave. Review and approve to confirm the new booking.
          </p>

          <div style={{ display: 'grid', gap: '8px' }}>
            {rebookings.map((rb) => (
              <div
                key={rb.id}
                style={{
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--bg)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge badge-opd">{rb.speciality} ({rb.visit_type})</span>
                    <span style={{ fontWeight: 600 }}>{rb.patient_name}</span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Proposed with {rb.doctor_name}</span>
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--ink)' }}>
                    New slot: <b>{rb.date} at {rb.start_time}–{rb.end_time}</b> · <span style={{ color: 'var(--muted)' }}>{rb.reason}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleApproveRebooking(rb.id)}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleRejectRebooking(rb.id)}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approvals Queue */}
      {approvals.length > 0 && (
        <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>
            Staff Approval Queue ({approvals.length} Pending)
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '12px' }}>
            Requests made inside the 2-hour cutoff window requiring staff review.
          </p>

          <div style={{ display: 'grid', gap: '8px' }}>
            {approvals.map((appr) => (
              <div
                key={appr.id}
                style={{
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--bg)',
                }}
              >
                <div>
                  <span className="badge badge-opd" style={{ marginRight: '8px' }}>{appr.kind}</span>
                  <span style={{ fontWeight: 600 }}>Appointment {appr.appointment_id}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleDecideApproval(appr.id, 'APPROVED')}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleDecideApproval(appr.id, 'REJECTED')}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Doctor Leave Rebookings Queue (R7) */}
      {rebookings.length > 0 && (
        <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
            Doctor Leave Rebooking Proposals ({rebookings.length} Pending Approval)
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '12px' }}>
            Automated rebooking proposals generated when doctors mark leave. Review and approve to confirm the new booking.
          </p>

          <div style={{ display: 'grid', gap: '8px' }}>
            {rebookings.map((rb) => (
              <div
                key={rb.id}
                style={{
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--bg)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge badge-opd">{rb.speciality} ({rb.visit_type})</span>
                    <span style={{ fontWeight: 600 }}>{rb.patient_name}</span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Proposed with {rb.doctor_name}</span>
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--ink)' }}>
                    New slot: <b>{rb.date} at {rb.start_time}–{rb.end_time}</b> · <span style={{ color: 'var(--muted)' }}>{rb.reason}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleApproveRebooking(rb.id)}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => handleRejectRebooking(rb.id)}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RAG Knowledge Base Search Debugger (Iteration 3 R2) */}
      <SearchDebugger />

      {/* Appointment Roster with Filters */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <h3 style={{ fontSize: '1.3rem' }}>Clinic Appointment Master List</h3>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 600 }}>Date:</label>
            <input
              type="date"
              className="form-control"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              style={{ width: '160px' }}
            />

            <label style={{ fontSize: '0.9rem', fontWeight: 600, marginLeft: '6px' }}>Doctor:</label>
            <select
              className="form-control"
              value={selectedDoctor}
              onChange={(e) => setSelectedDoctor(e.target.value)}
              style={{ width: '180px' }}
            >
              <option value="">All Doctors</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <p style={{ color: 'var(--muted)' }}>Loading appointments...</p>
        ) : appointments.length === 0 ? (
          <p style={{ color: 'var(--muted)' }}>No appointments found matching filters.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.92rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--line)' }}>
                  <th style={{ padding: '10px' }}>ID</th>
                  <th style={{ padding: '10px' }}>Time</th>
                  <th style={{ padding: '10px' }}>Patient</th>
                  <th style={{ padding: '10px' }}>Doctor</th>
                  <th style={{ padding: '10px' }}>Speciality</th>
                  <th style={{ padding: '10px' }}>Status</th>
                  <th style={{ padding: '10px' }}>Source</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => (
                  <tr key={a.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '10px' }} className="mono">{a.id}</td>
                    <td style={{ padding: '10px' }} className="mono">{a.start_time} - {a.end_time}</td>
                    <td style={{ padding: '10px', fontWeight: 600 }}>{a.patient_name} ({a.patient_id})</td>
                    <td style={{ padding: '10px' }}>{a.doctor_name}</td>
                    <td style={{ padding: '10px' }}>{a.speciality} ({a.visit_type})</td>
                    <td style={{ padding: '10px' }}>
                      <span className={`badge badge-${a.status}`}>{a.status}</span>
                    </td>
                    <td style={{ padding: '10px', fontSize: '0.8rem', color: 'var(--muted)' }}>Booked via {a.source}</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      {a.status === 'booked' && (
                        <button
                          className="btn btn-danger"
                          style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                          onClick={() => handleStaffCancel(a.id)}
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Walk-in Booking Modal */}
      {showWalkinModal && (
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
            <h3 style={{ fontSize: '1.4rem', marginBottom: '14px' }}>Book Walk-in / On-Behalf</h3>

            {walkinError && (
              <div style={{
                background: 'var(--danger-soft)',
                border: '1px solid var(--danger)',
                color: 'var(--danger)',
                padding: '10px',
                borderRadius: '8px',
                marginBottom: '12px',
                fontSize: '0.9rem',
              }}>
                {walkinError}
              </div>
            )}

            <form onSubmit={handleWalkinSubmit}>
              <div className="form-group">
                <label className="form-label">Search & Select Patient:</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Type name or mobile (e.g. Asha or 9000000001)..."
                  value={searchQuery}
                  onChange={(e) => handlePatientSearch(e.target.value)}
                />
                {patientsList.length > 0 && (
                  <select
                    className="form-control"
                    style={{ marginTop: '6px' }}
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                  >
                    {patientsList.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.mobile}) - {p.id}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Doctor & Speciality:</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <select
                    className="form-control"
                    value={walkinDocId}
                    onChange={(e) => {
                      setWalkinDocId(e.target.value);
                      const doc = doctors.find((d) => d.id === e.target.value);
                      if (doc) setWalkinSpec(doc.specialities[0]);
                    }}
                  >
                    {doctors.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>

                  <select
                    className="form-control"
                    value={walkinSpec}
                    onChange={(e) => setWalkinSpec(e.target.value)}
                  >
                    {doctors.find((d) => d.id === walkinDocId)?.specialities.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Visit Type & Date:</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <select
                    className="form-control"
                    value={walkinType}
                    onChange={(e) => setWalkinType(e.target.value)}
                  >
                    <option value="new">New (20 min)</option>
                    <option value="follow_up">Follow-up (10 min)</option>
                  </select>

                  <input
                    type="date"
                    className="form-control"
                    value={walkinDate}
                    onChange={(e) => setWalkinDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Time Slot:</label>
                <div className="slot-grid" style={{ maxHeight: '120px', overflowY: 'auto' }}>
                  {walkinSlots.map((s) => (
                    <button
                      type="button"
                      key={s.start_time}
                      className={`slot-btn ${walkinSlot === s.start_time ? 'selected' : ''}`}
                      onClick={() => setWalkinSlot(s.start_time)}
                    >
                      {s.start_time}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowWalkinModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!selectedPatientId || !walkinSlot}
                >
                  Confirm Walk-in Booking
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

