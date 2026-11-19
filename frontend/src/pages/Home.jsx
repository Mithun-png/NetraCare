import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api/client';
import NetraCareLogo from '../components/NetraCareLogo';
import {
  Clock,
  Calendar,
  AlertTriangle,
  ShieldCheck,
  ChevronRight,
  ChevronLeft,
  Plus,
  Stethoscope,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

const CLINICAL_SCENARIOS = [
  {
    time: '09:00 AM',
    title: 'Emergency screening',
    text: 'Walk in with acute flashes of light—instant triage flags urgent care.',
    tag: 'Safety First',
  },
  {
    time: '11:15 AM',
    title: 'Paediatric exam',
    text: 'Gentle strabismus evaluation with Dr. Vikram Menon and guardian.',
    tag: 'Paediatrics',
  },
  {
    time: '02:30 PM',
    title: 'Refractive intake',
    text: 'LASIK corneal thickness and suitability intake with Dr. Fatima Khan.',
    tag: 'Refractive',
  },
  {
    time: '04:45 PM',
    title: 'Cataract follow-up',
    text: 'Post-op lens clarity check and recovery drop schedule with Dr. Anita Roy.',
    tag: 'Cataract',
  },
  {
    time: '06:00 PM',
    title: 'Glaucoma check',
    text: 'Intraocular pressure reading and visual field analysis.',
    tag: 'Glaucoma',
  },
];

const CLINIC_FAQS = [
  {
    id: 'f1',
    q: 'How does NetraCare handle acute eye emergencies?',
    a: 'Our front desk software evaluates all patient queries for 5 acute ophthalmic red flags (sudden vision loss, chemical splash, penetrating trauma, severe acute eye pain, flashes/curtain). In any emergency, automated routine booking is halted, instant emergency care steps are shown, and an urgent alert is dispatched to clinic staff.',
  },
  {
    id: 'f2',
    q: 'What is the paediatric booking rule for patients under 16?',
    a: 'In accordance with clinical protocol, all patients under 16 years of age (e.g. Divya Pillai) are restricted strictly to Dr. Vikram Menon, our Paediatric Ophthalmology specialist. In addition, an adult guardian must accompany the patient during the visit.',
  },
  {
    id: 'f3',
    q: 'How are LASIK pre-assessment criteria verified?',
    a: 'Candidates for LASIK must be at least 18 years old, possess stable refractive prescription for 12 months, not be pregnant or nursing, and have healthy corneal thickness. Dr. Fatima Khan reviews your clinical intake notes prior to the detailed slit-lamp evaluation.',
  },
  {
    id: 'f4',
    q: 'Can I reschedule or cancel my appointment online?',
    a: 'Yes. Appointments can be rescheduled or cancelled freely up to 2 hours before the scheduled appointment start time via the Patient Portal or conversational assistant, ensuring slots can be opened for other patients in need.',
  },
  {
    id: 'f5',
    q: 'How are CityCare Hospital partner laboratory tests integrated?',
    a: 'NetraCare connects directly to CityCare Lab via Model Context Protocol (MCP). Patients can inquire about test preparation (e.g. fasting requirements for HbA1c, lipid profiles) and pricing with authoritative partner attribution.',
  },
];

export default function Home({ onNavigateToLogin, onNavigateToBook }) {
  const [clinic, setClinic] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [openFaq, setOpenFaq] = useState(null);

  const scenarioTrackRef = useRef(null);

  useEffect(() => {
    api.getClinicInfo().then(setClinic).catch(console.error);
    api.getDoctors().then(setDoctors).catch(console.error);
    api.getHolidays().then(setHolidays).catch(console.error);
  }, []);

  const scrollScenarios = (offset) => {
    if (scenarioTrackRef.current) {
      scenarioTrackRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  const toggleFaq = (id) => {
    setOpenFaq((prev) => (prev === id ? null : id));
  };

  return (
    <div
      className="container"
      style={{
        display: 'grid',
        gap: '48px',
        position: 'relative',
        width: '100%',
        maxWidth: '1040px',
        margin: '0 auto',
        boxSizing: 'border-box',
      }}
    >
      {/* =========================================================================
          HERO SECTION (Center-aligned, 2 large blurred blobs, 72px Outfit headline)
         ========================================================================= */}
      <section
        className="card reveal-on-scroll"
        style={{
          position: 'relative',
          padding: '64px 28px 56px 28px',
          textAlign: 'center',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '440px',
          width: '100%',
          boxSizing: 'border-box',
          minWidth: 0,
        }}
      >
        {/* Floating Blurred Ambient Blobs in 6s loop */}
        <div
          className="softly-blob softly-blob-peach"
          style={{
            top: '-80px',
            left: 'calc(50% - 320px)',
          }}
          aria-hidden="true"
        />
        <div
          className="softly-blob softly-blob-lavender"
          style={{
            top: '0px',
            right: 'calc(50% - 340px)',
          }}
          aria-hidden="true"
        />

        {/* Content Container Centered */}
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '780px', margin: '0 auto', width: '100%' }}>
          {/* Hero Title Card Badge with NetraCare Logo */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '12px',
              background: 'rgba(255, 255, 255, 0.92)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius-full)',
              padding: '6px 20px 6px 8px',
              marginBottom: '22px',
              boxShadow: 'var(--shadow-glass)',
            }}
          >
            <NetraCareLogo size={36} />
            <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)', display: 'block' }}>
                NetraCare Eye Clinic
              </span>
              <span style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '0.02em' }}>
                AI Front Desk & Clinical Care Coordination
              </span>
            </div>
          </div>

          {/* 72px Outfit Headline with Reenie Beanie Cursive Accent */}
          <h1
            style={{
              fontSize: 'clamp(2.4rem, 6vw, 4.2rem)',
              fontWeight: 600,
              lineHeight: 1.12,
              letterSpacing: '-0.025em',
              marginBottom: '20px',
              color: 'var(--ink)',
            }}
          >
            Ophthalmic care, guided with{' '}
            <span
              className="cursive"
              style={{
                fontSize: '1.25em',
                color: '#342F2D',
                padding: '0 4px',
                position: 'relative',
                display: 'inline-block',
              }}
            >
              gentle
              {/* Soft decorative underline */}
              <svg
                style={{
                  position: 'absolute',
                  bottom: '-4px',
                  left: '4px',
                  width: '100%',
                  height: '10px',
                  overflow: 'visible',
                }}
                viewBox="0 0 100 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M 2 8 C 30 2, 70 12, 98 4"
                  stroke="var(--accent)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </svg>
            </span>{' '}
            precision.
          </h1>

          {/* Sub-headline max-width 500px Centered */}
          <p
            style={{
              color: 'var(--muted)',
              fontSize: '1.1rem',
              lineHeight: 1.6,
              maxWidth: '520px',
              margin: '0 auto 32px auto',
            }}
          >
            Expert ophthalmic consultations across 5 superspecialists. Zero double-booking, guaranteed emergency triage, and seamless appointment coordination.
          </p>

          {/* Dual CTA Buttons Centered */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px',
              flexWrap: 'wrap',
              marginBottom: '32px',
            }}
          >
            <button className="btn btn-primary" onClick={onNavigateToBook} style={{ padding: '14px 32px' }}>
              Book appointment <ChevronRight size={16} />
            </button>
            <button className="btn btn-secondary" onClick={onNavigateToLogin} style={{ padding: '14px 28px' }}>
              Access portals
            </button>
          </div>

          {/* Clinical Indicators Centered */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '24px',
              fontSize: '13px',
              color: 'var(--muted)',
              flexWrap: 'wrap',
            }}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--accent)' }}>●</span> Zero double bookings guaranteed
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#2E5939' }}>●</span> Deterministic emergency triage
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#5C4E7C' }}>●</span> 5 accredited eye specialists
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          HORIZONTAL CLINICAL SCENARIOS SCROLL (Fully contained & responsive)
         ========================================================================= */}
      <section className="clinical-scenario-container" style={{ minWidth: 0, width: '100%', boxSizing: 'border-box' }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <span className="cursive" style={{ fontSize: '26px', color: 'var(--muted)' }}>
            daily clinic rhythms
          </span>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', marginTop: '2px' }}>
            A day inside the NetraCare front desk
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '1rem', maxWidth: '540px', margin: '8px auto 0 auto' }}>
            Explore how appointments, acute emergencies, and specialized intakes flow smoothly across our clinic.
          </p>
        </div>

        {/* Scrolling Card Track within bounds */}
        <div style={{ position: 'relative', width: '100%', minWidth: 0 }}>
          <div
            ref={scenarioTrackRef}
            className="clinical-scenario-track"
            tabIndex={0}
            role="region"
            aria-label="Clinical Scenarios"
          >
            {CLINICAL_SCENARIOS.map((item, idx) => (
              <div key={idx} className="clinical-scenario-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '14px', color: 'var(--muted)', fontWeight: 500 }}>
                    {item.time}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      color: 'var(--muted)',
                      background: 'var(--off)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                    }}
                  >
                    {item.tag}
                  </span>
                </div>

                <p className="scenario-text" style={{ fontSize: '18px', fontWeight: 500, lineHeight: 1.35, color: 'var(--ink)' }}>
                  {item.text}
                </p>
              </div>
            ))}
          </div>

          {/* Centered Scroll Controls */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '12px' }}>
            <button
              onClick={() => scrollScenarios(-300)}
              className="btn btn-secondary"
              style={{ width: '40px', height: '40px', padding: 0, borderRadius: '50%' }}
              aria-label="Scroll left"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              onClick={() => scrollScenarios(300)}
              className="btn btn-secondary"
              style={{ width: '40px', height: '40px', padding: 0, borderRadius: '50%' }}
              aria-label="Scroll right"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          CLINIC HOURS & RULES ENFORCED (Centered Responsive Grid)
         ========================================================================= */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '24px',
          width: '100%',
          minWidth: 0,
        }}
      >
        {/* Hours & Sessions */}
        <div className="card" style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-soft)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#C85348',
              }}
            >
              <Clock size={18} />
            </div>
            <h3>Clinic Timings & Sessions</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'grid', gap: '10px', fontSize: '0.96rem' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
              <span style={{ color: 'var(--muted)' }}>Operating Days</span>
              <b>Monday to Saturday</b>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
              <span style={{ color: 'var(--muted)' }}>Morning Session</span>
              <b>09:00 AM – 01:00 PM</b>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
              <span style={{ color: 'var(--muted)' }}>Lunch Intermission</span>
              <span style={{ color: 'var(--muted)' }}>01:00 PM – 02:00 PM (Closed)</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
              <span style={{ color: 'var(--muted)' }}>Evening Session</span>
              <b>02:00 PM – 06:00 PM</b>
            </li>
            <li style={{ color: 'var(--danger)', fontWeight: 500, paddingTop: '4px' }}>
              Closed on Sundays and Listed Public Holidays
            </li>
          </ul>
        </div>

        {/* Rules Enforced */}
        <div className="card" style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--sage)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--sage-ink)',
              }}
            >
              <ShieldCheck size={18} />
            </div>
            <h3>Clinical Rules Enforced</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'grid', gap: '10px', fontSize: '0.96rem' }}>
            <li>✓ <b>New Consultation:</b> 20 minutes allocated duration</li>
            <li>✓ <b>Follow-up Visit:</b> 10 minutes with previous specialist</li>
            <li>✓ <b>Paediatric Age Gate:</b> Patients under 16 strictly with Dr. Vikram Menon</li>
            <li>✓ <b>Cancellation Window:</b> Up to 2 hours before scheduled slot</li>
            <li>✓ <b>Safety Rule:</b> Immediate triage and lockout for red-flag symptoms</li>
          </ul>
        </div>
      </div>

      {/* =========================================================================
          DOCTORS & SPECIALITIES (Centered Header, Responsive Grid)
         ========================================================================= */}
      <section id="doctors" className="card" style={{ minWidth: 0, width: '100%', boxSizing: 'border-box' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <span className="cursive" style={{ fontSize: '26px', color: 'var(--muted)' }}>
            accredited clinicians
          </span>
          <h3 style={{ fontSize: '1.9rem', marginTop: '2px' }}>Our Doctors & Superspecialities</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.98rem', marginTop: '6px' }}>
            Five specialist ophthalmologists providing comprehensive medical, surgical, and paediatric eye care.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', width: '100%' }}>
          {doctors.map((doc) => (
            <div
              key={doc.id}
              style={{
                border: '1px solid var(--line)',
                borderRadius: '18px',
                padding: '20px',
                background: 'var(--surface)',
                boxShadow: 'var(--shadow-soft)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span className="mono" style={{ fontWeight: 600, color: '#C85348' }}>
                    {doc.id}
                  </span>
                  <span className="badge badge-opd">Active</span>
                </div>
                <h4 style={{ fontSize: '1.2rem', marginBottom: '10px' }}>{doc.name}</h4>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '12px' }}>
                {doc.specialities.map((spec) => (
                  <span
                    key={spec}
                    style={{
                      fontSize: '0.8rem',
                      background: 'var(--off)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-full)',
                      border: '1px solid var(--line)',
                      color: 'var(--ink)',
                    }}
                  >
                    {spec}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* =========================================================================
          WEEKLY OPD SCHEDULE GRID (Contained within schedule-table-wrapper)
         ========================================================================= */}
      <section id="schedule" className="card" style={{ minWidth: 0, width: '100%', boxSizing: 'border-box' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <span className="cursive" style={{ fontSize: '26px', color: 'var(--muted)' }}>
            rotation timetable
          </span>
          <h3 style={{ fontSize: '1.9rem', marginTop: '2px' }}>Weekly OPD Grid</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.98rem', marginTop: '6px' }}>
            Doctors conduct Outpatient Consultations (OPD), Surgeries (SX), or have scheduled off days.
          </p>
        </div>

        {/* Contained responsive table wrapper */}
        <div className="schedule-table-wrapper">
          <table className="schedule-table">
            <thead>
              <tr style={{ background: 'var(--off)', borderBottom: '1px solid var(--line)' }}>
                <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: 600 }}>Doctor</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Mon</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Tue</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Wed</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Thu</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Fri</th>
                <th style={{ padding: '14px 10px', fontWeight: 600 }}>Sat</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--line)' }}>
                <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Dr. Anand Rao</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--line)' }}>
                <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Dr. Meera Iyer</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--line)' }}>
                <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Dr. Kiran Shah</td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-off">OFF</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--line)' }}>
                <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Dr. Fatima Khan</td>
                <td><span className="badge badge-sx">SX</span> <span className="badge badge-sx">SX</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
                <td><span className="badge badge-opd">AM</span> <span className="badge badge-opd">PM</span></td>
              </tr>
              <tr>
                <td style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Dr. Vikram Menon</td>
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

      {/* =========================================================================
          INTERACTIVE FAQ ACCORDION (Centered Header & Container)
         ========================================================================= */}
      <section id="faq" style={{ minWidth: 0, width: '100%', boxSizing: 'border-box' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span className="cursive" style={{ fontSize: '26px', color: 'var(--muted)' }}>
            patient guidance
          </span>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', marginTop: '2px' }}>
            Frequently Asked Clinic Questions
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '1rem', marginTop: '6px' }}>
            Everything you need to know about our safety screening, doctor appointments, and procedures.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '820px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
          {CLINIC_FAQS.map((faq) => {
            const isOpen = openFaq === faq.id;

            return (
              <div key={faq.id} className="softly-faq-box">
                <button
                  className="softly-faq-btn"
                  onClick={() => toggleFaq(faq.id)}
                  aria-expanded={isOpen}
                >
                  <span style={{ paddingRight: '16px', lineHeight: 1.4 }}>{faq.q}</span>
                  <div className={`softly-faq-rotator ${isOpen ? 'expanded' : ''}`}>
                    <Plus size={18} />
                  </div>
                </button>

                <div
                  className="softly-faq-panel"
                  style={{
                    maxHeight: isOpen ? '260px' : '0px',
                    opacity: isOpen ? 1 : 0,
                  }}
                >
                  <div className="softly-faq-panel-inner">{faq.a}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* =========================================================================
          WAITLIST / BOOKING CONVERSION SECTION (Centered & Contained)
         ========================================================================= */}
      <section
        className="card"
        style={{
          background: 'linear-gradient(180deg, #FFFFFF 0%, #FAFAF7 100%)',
          borderRadius: 'var(--radius-xl)',
          padding: '56px 28px',
          textAlign: 'center',
          boxShadow: 'var(--shadow-lg)',
          position: 'relative',
          overflow: 'hidden',
          maxWidth: '820px',
          margin: '0 auto',
          width: '100%',
          boxSizing: 'border-box',
          minWidth: 0,
        }}
      >
        {/* NetraCare Emblem Title Card Badge */}
        <div
          style={{
            margin: '0 auto 20px auto',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '6px',
            borderRadius: '24px',
            background: 'rgba(255, 255, 255, 0.95)',
            boxShadow: 'var(--shadow-glass)',
            border: '1px solid var(--line)',
          }}
          aria-hidden="true"
        >
          <NetraCareLogo size={52} />
        </div>

        <span className="cursive" style={{ fontSize: '26px', color: 'var(--muted)', display: 'block' }}>
          seamless care coordination
        </span>

        <h2 style={{ fontSize: 'clamp(2rem, 4.5vw, 2.75rem)', marginBottom: '12px' }}>
          Schedule your consultation with peace of mind
        </h2>

        <p style={{ color: 'var(--muted)', fontSize: '1.05rem', maxWidth: '520px', margin: '0 auto 28px auto' }}>
          Select your specialist, find guaranteed slots up to 30 days ahead, and receive personalized pre-visit care instructions.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={onNavigateToBook} style={{ padding: '16px 36px', fontSize: '1rem' }}>
            Book Appointment Now <ChevronRight size={16} />
          </button>
          <button className="btn btn-secondary" onClick={onNavigateToLogin} style={{ padding: '16px 28px', fontSize: '1rem' }}>
            Patient Portal Login
          </button>
        </div>

        <div
          style={{
            marginTop: '28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--muted)',
          }}
        >
          <ShieldCheck size={14} />
          <span>Zero double booking · Verified doctor availability · Clinic confidential</span>
        </div>
      </section>
    </div>
  );
}
