import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { api } from '../api/client';
import {
  Send,
  Paperclip,
  RotateCcw,
  AlertTriangle,
  BookOpen,
  CheckCircle,
  XCircle,
  FileText,
  Clock,
  UserCheck,
  ChevronRight,
  Maximize2,
  X,
} from 'lucide-react';

export default function ChatWindow({ mode = 'full', onExpand }) {
  const {
    messages,
    loading,
    error,
    pendingAction,
    pendingOcrDraft,
    setPendingOcrDraft,
    sendMessage,
    confirmAction,
    selectHitlOption,
    attachOcrTextToChat,
    resetChat,
  } = useChat();

  const [input, setInput] = useState('');
  const [uploadingOcr, setUploadingOcr] = useState(false);
  const [ocrError, setOcrError] = useState('');
  const [editableOcrText, setEditableOcrText] = useState('');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingAction, pendingOcrDraft]);

  useEffect(() => {
    if (pendingOcrDraft) {
      setEditableOcrText(pendingOcrDraft.formatted_summary || pendingOcrDraft.raw_text || '');
    }
  }, [pendingOcrDraft]);

  const quickQuestions = [
    "Book my retina follow-up with Dr. Shah this Friday morning. Reason: diabetic eye review",
    "What appointments do I have?",
    "How much is a new consultation?",
    "Book a glaucoma check with Dr. Iyer this Thursday",
    "Is there parking at the clinic?",
  ];

  const handleSend = (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput('');
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingOcr(true);
    setOcrError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.uploadOcrPrescription(formData);
      if (res.red_flag) {
        setOcrError(res.emergency_response || 'Emergency symptoms detected in document.');
      } else {
        setPendingOcrDraft(res);
      }
    } catch (err) {
      setOcrError(err.message || 'Failed to process document OCR.');
    } finally {
      setUploadingOcr(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const isWidget = mode === 'widget';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: isWidget ? '100%' : '650px',
        maxHeight: isWidget ? '100%' : '80vh',
        background: 'var(--surface, #ffffff)',
        borderRadius: isWidget ? '0' : '24px',
        border: isWidget ? 'none' : '1px solid var(--border, rgba(0,0,0,0.06))',
        boxShadow: isWidget ? 'none' : '0 12px 36px rgba(0,0,0,0.05)',
        overflow: 'hidden',
      }}
    >
      {/* Header for Widget Mode */}
      {isWidget && (
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid var(--border, rgba(0,0,0,0.06))',
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(253, 252, 248, 0.9))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
              }}
            />
            <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--ink, #292524)' }}>
              NetraCare Front Desk
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {onExpand && (
              <button
                type="button"
                onClick={onExpand}
                title="Expand to Full View"
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--muted, #78716c)',
                  padding: '4px',
                  display: 'flex',
                }}
              >
                <Maximize2 size={16} />
              </button>
            )}
            <button
              type="button"
              onClick={resetChat}
              title="Reset conversation"
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--muted, #78716c)',
                padding: '4px',
                display: 'flex',
              }}
            >
              <RotateCcw size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: isWidget ? '16px' : '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: isWidget ? '20px 10px' : '40px 20px', color: 'var(--muted)' }}>
            <h4 style={{ fontSize: isWidget ? '1.1rem' : '1.3rem', marginBottom: '8px', color: 'var(--ink, #292524)' }}>
              Welcome to NetraCare Front Desk
            </h4>
            <p style={{ fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto 20px', lineHeight: 1.5 }}>
              Ask about doctor schedules, appointments, clinic guidelines, or upload a prescription for OCR.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              {quickQuestions.slice(0, isWidget ? 3 : 5).map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => sendMessage(q)}
                  style={{
                    background: 'var(--bg, #FDFCF8)',
                    border: '1px solid var(--border, rgba(0,0,0,0.08))',
                    padding: '8px 14px',
                    borderRadius: '20px',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    color: 'var(--ink, #292524)',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = 'var(--coral, #FFB7B2)';
                    e.currentTarget.style.background = '#ffffff';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border, rgba(0,0,0,0.08))';
                    e.currentTarget.style.background = 'var(--bg, #FDFCF8)';
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, idx) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '100%',
              }}
            >
              <div
                style={{
                  maxWidth: isWidget ? '88%' : '78%',
                  padding: '12px 18px',
                  borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                  background: isUser
                    ? 'linear-gradient(135deg, var(--ink, #292524), #1c1917)'
                    : m.emergency
                    ? '#fef2f2'
                    : 'var(--bg, #FDFCF8)',
                  color: isUser ? '#ffffff' : m.emergency ? '#991b1b' : 'var(--ink, #292524)',
                  border: isUser
                    ? 'none'
                    : m.emergency
                    ? '1px solid #fecaca'
                    : '1px solid var(--border, rgba(0,0,0,0.07))',
                  fontSize: '0.92rem',
                  lineHeight: 1.55,
                  whiteSpace: 'pre-wrap',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                }}
              >
                {m.emergency && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '6px', color: '#dc2626' }}>
                    <AlertTriangle size={18} />
                    <span>Clinical Emergency Protocol</span>
                  </div>
                )}
                {m.content}
              </div>

              {/* Source tags */}
              {!isUser && m.sources && m.sources.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px', marginLeft: '6px' }}>
                  {m.sources.map((src, sIdx) => (
                    <span
                      key={sIdx}
                      style={{
                        fontSize: '0.74rem',
                        padding: '2px 8px',
                        background: 'rgba(0,0,0,0.04)',
                        borderRadius: '12px',
                        color: 'var(--muted, #78716c)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <BookOpen size={10} />
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Pending OCR Draft Card */}
        {pendingOcrDraft && (
          <div
            style={{
              padding: '16px',
              borderRadius: '18px',
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              boxShadow: '0 4px 14px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#0f172a' }}>
              <FileText size={18} color="#0284c7" />
              <strong style={{ fontSize: '0.92rem' }}>Prescription OCR Transcription Preview</strong>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '8px' }}>
              Review or adjust transcribed optical markers before attaching to your appointment notes.
            </p>
            <textarea
              value={editableOcrText}
              onChange={(e) => setEditableOcrText(e.target.value)}
              rows={5}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '10px',
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
                fontFamily: 'monospace',
                background: '#ffffff',
                boxSizing: 'border-box',
                resize: 'vertical',
                marginBottom: '10px',
              }}
            />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setPendingOcrDraft(null)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '16px',
                  border: '1px solid #cbd5e1',
                  background: '#ffffff',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                Discard
              </button>
              <button
                type="button"
                onClick={() => attachOcrTextToChat(editableOcrText)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '16px',
                  border: 'none',
                  background: 'var(--coral, #FFB7B2)',
                  color: 'var(--ink, #292524)',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                Attach to Chat
              </button>
            </div>
          </div>
        )}

        {/* Interactive Action Card: Standard Confirmation */}
        {pendingAction && pendingAction.action === 'book' && (
          <div
            style={{
              padding: '18px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #ffffff, var(--bg, #FDFCF8))',
              border: '1.5px solid var(--coral, #FFB7B2)',
              boxShadow: '0 8px 24px rgba(255, 183, 178, 0.25)',
              margin: '6px 0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Clock size={18} color="var(--ink, #292524)" />
              <strong style={{ fontSize: '0.95rem', color: 'var(--ink, #292524)' }}>Please Confirm Appointment</strong>
            </div>
            <p style={{ fontSize: '0.9rem', marginBottom: '14px', color: 'var(--ink, #292524)' }}>
              {pendingAction.summary}
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                disabled={loading}
                onClick={() => confirmAction(true)}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '24px',
                  background: 'var(--coral, #FFB7B2)',
                  border: 'none',
                  fontWeight: 600,
                  color: 'var(--ink, #292524)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <CheckCircle size={16} />
                Confirm & Book
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => confirmAction(false)}
                style={{
                  padding: '10px 16px',
                  borderRadius: '24px',
                  background: 'transparent',
                  border: '1px solid var(--border, rgba(0,0,0,0.15))',
                  color: 'var(--muted, #78716c)',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Interactive Action Card: HITL Doctor Unavailable Re-routing */}
        {pendingAction && pendingAction.type === 'HITL_DOCTOR_UNAVAILABLE' && (
          <div
            style={{
              padding: '18px',
              borderRadius: '20px',
              background: '#ffffff',
              border: '1.5px solid #f59e0b',
              boxShadow: '0 8px 24px rgba(245, 158, 11, 0.15)',
              margin: '6px 0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <AlertTriangle size={18} color="#d97706" />
              <strong style={{ fontSize: '0.95rem', color: '#b45309' }}>Doctor Unavailable — Alternative Options</strong>
            </div>
            <p style={{ fontSize: '0.9rem', marginBottom: '14px', color: 'var(--ink, #292524)', lineHeight: 1.5 }}>
              {pendingAction.message}
            </p>

            {pendingAction.options?.map((opt, oIdx) => (
              <div key={oIdx} style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#78716c', marginBottom: '6px' }}>
                  {opt.label}:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {opt.slots?.map((slot, sIdx) => (
                    <button
                      key={sIdx}
                      type="button"
                      disabled={loading}
                      onClick={() => selectHitlOption(slot)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '12px',
                        background: 'var(--bg, #FDFCF8)',
                        border: '1px solid var(--border, rgba(0,0,0,0.1))',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '0.85rem',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.borderColor = 'var(--coral, #FFB7B2)';
                        e.currentTarget.style.background = '#ffffff';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border, rgba(0,0,0,0.1))';
                        e.currentTarget.style.background = 'var(--bg, #FDFCF8)';
                      }}
                    >
                      <span>
                        <strong>{slot.doctor_name}</strong> • {slot.date} at {slot.start_time}
                      </span>
                      <ChevronRight size={14} color="#78716c" />
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--muted)', fontSize: '0.85rem', padding: '6px 10px' }}>
            <div className="spinner" style={{ width: '14px', height: '14px' }} />
            <span>Consulting clinic front desk...</span>
          </div>
        )}

        {(error || ocrError) && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '12px',
              background: '#fef2f2',
              color: '#b91c1c',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertTriangle size={16} />
            <span>{error || ocrError}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSend}
        style={{
          padding: isWidget ? '10px 14px' : '16px 20px',
          borderTop: '1px solid var(--border, rgba(0,0,0,0.06))',
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(253, 252, 248, 0.9))',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="image/jpeg,image/png,image/webp,application/pdf"
          style={{ display: 'none' }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadingOcr || loading}
          title="Upload Prescription / Referral (OCR)"
          style={{
            background: 'transparent',
            border: 'none',
            color: uploadingOcr ? 'var(--coral, #FFB7B2)' : 'var(--muted, #78716c)',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.15s ease',
          }}
        >
          <Paperclip size={18} />
        </button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={uploadingOcr ? 'Processing document OCR...' : 'Type symptoms, booking request, or question...'}
          disabled={loading || uploadingOcr}
          style={{
            flex: 1,
            padding: '10px 16px',
            borderRadius: '24px',
            border: '1px solid var(--border, rgba(0,0,0,0.12))',
            background: '#ffffff',
            fontSize: '0.9rem',
            color: 'var(--ink, #292524)',
            outline: 'none',
          }}
        />

        <button
          type="submit"
          disabled={!input.trim() || loading}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            border: 'none',
            background: input.trim() && !loading ? 'var(--ink, #292524)' : 'rgba(0,0,0,0.08)',
            color: input.trim() && !loading ? 'var(--coral, #FFB7B2)' : '#9ca3af',
            cursor: input.trim() && !loading ? 'pointer' : 'default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease',
          }}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
