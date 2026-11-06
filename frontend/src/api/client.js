/**
 * NetraCare API Client.
 * Automatically injects the X-Session-Data header from localStorage.
 */

const API_BASE = '/api/v1';

function getSessionToken() {
  return localStorage.getItem('netracare_session_token');
}

async function request(endpoint, options = {}) {
  const token = getSessionToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'X-Session-Data': token } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(data.detail?.message || data.detail || 'An error occurred');
    error.status = response.status;
    error.data = data.detail || data;
    error.reason_code = data.detail?.reason_code || null;
    throw error;
  }

  return data;
}

export const api = {
  // Auth
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  getMe: () => request('/auth/me'),

  // Public
  getClinicInfo: () => request('/public/clinic'),
  getDoctors: () => request('/public/doctors'),
  getSlots: (doctorId, date, visitType = 'new') =>
    request(`/public/slots?doctor_id=${encodeURIComponent(doctorId)}&date=${encodeURIComponent(date)}&visit_type=${encodeURIComponent(visitType)}`),
  getHolidays: () => request('/public/holidays'),
  getFactOfTheDay: (previous) =>
    request(previous ? `/public/fact-of-the-day?previous=${encodeURIComponent(previous)}` : '/public/fact-of-the-day'),

  // Patient
  getMyAppointments: () => request('/patient/appointments'),
  bookAppointment: (payload) => request('/patient/appointments', { method: 'POST', body: JSON.stringify(payload) }),
  cancelMyAppointment: (id, reason) =>
    request(`/patient/appointments/${encodeURIComponent(id)}/cancel`, { method: 'POST', body: JSON.stringify({ reason }) }),
  rescheduleMyAppointment: (id, payload) =>
    request(`/patient/appointments/${encodeURIComponent(id)}/reschedule`, { method: 'POST', body: JSON.stringify(payload) }),
  getPatientProfile: () => request('/patient/profile'),
  patientChat: (payload) =>
    request('/patient/chat', {
      method: 'POST',
      body: JSON.stringify(typeof payload === 'string' ? { message: payload } : payload),
    }),

  // Doctor
  getDoctorSchedule: (date) => request(date ? `/doctor/schedule?date=${encodeURIComponent(date)}` : '/doctor/schedule'),
  getDoctorAppointment: (id) => request(`/doctor/appointments/${encodeURIComponent(id)}`),
  getDoctorPatientSummary: (id) => request(`/doctor/appointments/${encodeURIComponent(id)}/summary`),
  completeVisit: (id, doctorNote) =>
    request(`/doctor/appointments/${encodeURIComponent(id)}/complete`, { method: 'POST', body: JSON.stringify({ doctor_note: doctorNote }) }),
  markDoctorLeave: (payload) =>
    request('/doctor/leave', { method: 'POST', body: JSON.stringify(payload) }),
  getDoctorLeaves: () => request('/doctor/leaves'),

  // Staff
  getStaffAppointments: (params = {}) => {
    const q = new URLSearchParams();
    if (params.date) q.append('date', params.date);
    if (params.doctor_id) q.append('doctor_id', params.doctor_id);
    if (params.status) q.append('status', params.status);
    return request(`/staff/appointments?${q.toString()}`);
  },
  staffBookAppointment: (payload) => request('/staff/appointments', { method: 'POST', body: JSON.stringify(payload) }),
  staffCancelAppointment: (id, reason) =>
    request(`/staff/appointments/${encodeURIComponent(id)}/cancel`, { method: 'POST', body: JSON.stringify({ reason }) }),
  getUrgentCases: () => request('/staff/urgent'),
  markUrgentSeen: (id) => request(`/staff/urgent/${encodeURIComponent(id)}/seen`, { method: 'POST' }),
  getApprovals: () => request('/staff/approvals'),
  approveApproval: (id) =>
    request(`/staff/approvals/${encodeURIComponent(id)}/approve`, { method: 'POST' }),
  rejectApproval: (id) =>
    request(`/staff/approvals/${encodeURIComponent(id)}/reject`, { method: 'POST' }),
  decideApproval: (id, decision, reason) =>
    request(`/staff/approvals/${encodeURIComponent(id)}/decide`, { method: 'POST', body: JSON.stringify({ decision, reason }) }),
  getStaffRebookings: () => request('/staff/rebookings'),
  approveRebooking: (id) =>
    request(`/staff/rebookings/${encodeURIComponent(id)}/approve`, { method: 'POST' }),
  rejectRebooking: (id) =>
    request(`/staff/rebookings/${encodeURIComponent(id)}/reject`, { method: 'POST' }),
  searchPatients: (q) => request(`/staff/patients${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  getSearchDebug: (q) => request(`/staff/search-debug?q=${encodeURIComponent(q)}`),
};

