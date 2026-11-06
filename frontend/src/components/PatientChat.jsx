import React, { useState } from 'react';
import { MessageSquare, Send, RotateCcw, AlertTriangle, BookOpen, Sparkles } from 'lucide-react';
import { api } from '../api/client';

export default function PatientChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const quickQuestions = [
    "What time does the clinic open on Saturday?",
    "How much does cataract surgery cost?",
    "Is it safe to ride my scooter after dilating drops?",
    "My optician said the pressure in my eyes is high",
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

    try {
      // Send last 6 messages as history
      const historyPayload = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.patientChat(text, historyPayload);

      const botMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        emergency: res.emergency || false,
        answered: res.answered !== false,
      };

      setMessages([...newHistory, botMsg]);
    } catch (err) {
      setError(err.message || "We couldn't check your message just now. Please try again, or call the clinic if it's urgent.");
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
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Ask NetraCare Assistant</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
              Answers from official clinic documents with citations & speciality guidance
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
            <Sparkles size={14} color="var(--accent)" /> Quick questions you can ask:
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
          minHeight: '220px',
          maxHeight: '380px',
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
              gap: '6px',
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
            Checking clinic knowledge base...
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
            placeholder="Ask about timings, fees, cataract, LASIK, or describe an eye concern..."
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
          <span>Enter to send · Answers strictly ground in NetraCare clinic documents</span>
          <span style={{ color: input.length > 450 ? 'var(--danger)' : 'var(--muted)' }}>
            {input.length}/500
          </span>
        </div>
      </div>
    </div>
  );
}

