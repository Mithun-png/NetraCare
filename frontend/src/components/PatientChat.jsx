import React, { useState } from 'react';
import { MessageSquare, Send, RotateCcw, AlertTriangle, BookOpen, Sparkles, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../api/client';

export default function PatientChat() {
  const [messages, setMessages] = useState([]);
  const [threadId, setThreadId] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const quickQuestions = [
    "Book my retina follow-up with Dr. Shah this Friday morning. Reason: diabetic eye review",
    "What appointments do I have?",
    "How much is a new consultation?",
    "Book a glaucoma check with Dr. Iyer this Thursday",
    "Is there parking at the clinic?",
  ];

  const handleSend = async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    if (text.length > 500) {
      setError('Message must be 500 characters or fewer.');
      return;
    }

    setError('');
    const userMsg = { role: 'user', content: text };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput('');
    setLoading(true);
    setPendingAction(null);

    try {
      const payload = {
        message: text,
        thread_id: threadId || undefined,
      };

      const res = await api.patientChat(payload);
      if (res.thread_id) {
        setThreadId(res.thread_id);
      }

      const botMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        emergency: res.emergency || false,
        pending_action: res.pending_action || null,
      };

      setMessages([...newHistory, botMsg]);
      if (res.pending_action) {
        setPendingAction(res.pending_action);
      }
    } catch (err) {
      setError(err.message || "We couldn't check your message just now. Please try again, or call the clinic if it's urgent.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (confirmed) => {
    if (loading || !threadId) return;

    setError('');
    setLoading(true);
    setPendingAction(null);

    const actionText = confirmed ? 'Confirm' : 'No';
    const userMsg = { role: 'user', content: actionText };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);

    try {
      const payload = {
        thread_id: threadId,
        confirm: confirmed,
      };

      const res = await api.patientChat(payload);
      const botMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        emergency: res.emergency || false,
        pending_action: res.pending_action || null,
      };

      setMessages([...newHistory, botMsg]);
      if (res.pending_action) {
        setPendingAction(res.pending_action);
      }
    } catch (err) {
      setError(err.message || "We couldn't process your confirmation just now. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setThreadId('');
    setPendingAction(null);
    setInput('');
    setError('');
  };

  return (
    <div className="card" style={{ display: 'grid', gap: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: 'var(--accent-soft)', color: 'var(--accent)', padding: '6px', borderRadius: '8px' }}>
            <MessageSquare size={20} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>NetraCare Booking Assistant</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
              Find slots, book, reschedule, cancel, and check clinic policies in real-time
            </span>
          </div>
        </div>
        <button
          onClick={handleNewChat}
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '0.85rem' }}
          title="Clear chat and start fresh"
        >
          <RotateCcw size={14} /> New Chat
        </button>
      </div>

      {/* Suggested Questions */}
      {messages.length === 0 && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--muted)' }}>
            <Sparkles size={14} color="var(--accent)" /> Examples you can try:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                style={{
                  background: 'var(--accent-soft)',
                  color: 'var(--accent)',
                  border: '1px solid var(--line)',
                  borderRadius: '20px',
                  padding: '6px 12px',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div
        style={{
          minHeight: '260px',
          maxHeight: '440px',
          overflowY: 'auto',
          display: 'grid',
          gap: '12px',
          paddingRight: '6px',
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              justifySelf: m.role === 'user' ? 'end' : 'start',
              maxWidth: '85%',
              background: m.role === 'user'
                ? 'var(--accent)'
                : m.emergency
                ? 'var(--danger-soft)'
                : 'var(--bg)',
              color: m.role === 'user' ? '#ffffff' : 'var(--ink)',
              border: m.emergency ? '2px solid var(--danger)' : '1px solid var(--line)',
              borderRadius: m.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              padding: '12px 16px',
              display: 'grid',
              gap: '8px',
            }}
          >
            {m.emergency && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--danger)', fontWeight: 700, fontSize: '0.9rem' }}>
                <AlertTriangle size={16} /> EMERGENCY ALERT
              </div>
            )}
            <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
              {m.content}
            </p>

            {/* Confirmation Card (R5) */}
            {m.pending_action && idx === messages.length - 1 && (
              <div
                style={{
                  background: 'var(--surface)',
                  border: '2px solid var(--accent)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  display: 'grid',
                  gap: '10px',
                  marginTop: '4px',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--ink)' }}>
                  {m.pending_action.summary}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleConfirm(true)}
                    disabled={loading}
                    className="btn btn-primary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      fontSize: '0.9rem',
                    }}
                  >
                    <CheckCircle size={16} /> Confirm
                  </button>
                  <button
                    onClick={() => handleConfirm(false)}
                    disabled={loading}
                    className="btn btn-secondary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      fontSize: '0.9rem',
                      color: 'var(--danger)',
                    }}
                  >
                    <XCircle size={16} /> No
                  </button>
                </div>
              </div>
            )}

            {m.sources && m.sources.length > 0 && (
              <div style={{ borderTop: '1px dashed var(--line)', paddingTop: '6px', marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <BookOpen size={12} /> Sources:
                </span>
                {m.sources.map((src, sIdx) => (
                  <span
                    key={sIdx}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.74rem',
                      background: 'var(--surface)',
                      color: 'var(--accent)',
                      border: '1px solid var(--line)',
                      borderRadius: '4px',
                      padding: '2px 6px',
                    }}
                  >
                    {src}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ justifySelf: 'start', background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: '12px', padding: '10px 14px', fontSize: '0.88rem', color: 'var(--muted)' }}>
            Processing with clinic assistant...
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.88rem' }}>
          {error}
        </div>
      )}

      {/* Input area */}
      <div style={{ display: 'grid', gap: '4px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            className="input"
            placeholder={pendingAction ? "Type a new question or press Confirm / No on the card..." : "Ask to find slots, book, cancel, reschedule, or ask a question..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            maxLength={500}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Send size={16} /> Send
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--muted)', paddingInline: '4px' }}>
          <span>Enter to send · Write actions always wait for your confirmation</span>
          <span style={{ color: input.length > 450 ? 'var(--danger)' : 'var(--muted)' }}>
            {input.length}/500
          </span>
        </div>
      </div>
    </div>
  );
}
