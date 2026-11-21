import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const ChatContext = createContext(null);

const STORAGE_KEY_THREAD = 'netracare_chat_thread_id';
const STORAGE_KEY_MSGS = 'netracare_chat_messages';

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY_MSGS);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [threadId, setThreadId] = useState(() => {
    try {
      return sessionStorage.getItem(STORAGE_KEY_THREAD) || '';
    } catch {
      return '';
    }
  });

  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const [pendingOcrDraft, setPendingOcrDraft] = useState(null);

  // Sync to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY_MSGS, JSON.stringify(messages));
    } catch {}
  }, [messages]);

  useEffect(() => {
    try {
      if (threadId) {
        sessionStorage.setItem(STORAGE_KEY_THREAD, threadId);
      }
    } catch {}
  }, [threadId]);

  const sendMessage = async (textToSend) => {
    const text = (textToSend || '').trim();
    if (!text || loading) return;

    if (text.length > 500) {
      setError('Message must be 500 characters or fewer.');
      return;
    }

    setError('');
    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
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
        timestamp: new Date().toISOString(),
      };

      setMessages([...newHistory, botMsg]);
      if (res.pending_action) {
        setPendingAction(res.pending_action);
      }
    } catch (err) {
      setError(err.message || "We couldn't check your message just now. Please try again or call the clinic.");
    } finally {
      setLoading(false);
    }
  };

  const confirmAction = async (confirmed) => {
    if (loading || !threadId) return;

    setError('');
    setLoading(true);
    const actionText = confirmed ? 'Confirm' : 'No, cancel';
    const userMsg = { role: 'user', content: actionText, timestamp: new Date().toISOString() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setPendingAction(null);

    try {
      const res = await api.patientChat({
        thread_id: threadId,
        confirm: confirmed,
      });

      const botMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        emergency: res.emergency || false,
        pending_action: res.pending_action || null,
        timestamp: new Date().toISOString(),
      };

      setMessages([...newHistory, botMsg]);
      if (res.pending_action) {
        setPendingAction(res.pending_action);
      }
    } catch (err) {
      setError(err.message || 'Error processing confirmation.');
    } finally {
      setLoading(false);
    }
  };

  const selectHitlOption = async (slot) => {
    if (loading || !threadId) return;

    setError('');
    setLoading(true);
    const slotSummary = `${slot.doctor_name} on ${slot.date} at ${slot.start_time}`;
    const userMsg = { role: 'user', content: `Selected: ${slotSummary}`, timestamp: new Date().toISOString() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setPendingAction(null);

    try {
      const res = await api.patientChat({
        thread_id: threadId,
        selected_option: slot,
      });

      const botMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        emergency: res.emergency || false,
        pending_action: res.pending_action || null,
        timestamp: new Date().toISOString(),
      };

      setMessages([...newHistory, botMsg]);
      if (res.pending_action) {
        setPendingAction(res.pending_action);
      }
    } catch (err) {
      setError(err.message || 'Error updating selection.');
    } finally {
      setLoading(false);
    }
  };

  const attachOcrTextToChat = (ocrFormattedText) => {
    const ocrMsg = {
      role: 'user',
      content: `[Attached Prescription/Referral]:\n${ocrFormattedText}`,
      timestamp: new Date().toISOString(),
      isOcr: true,
    };
    setMessages((prev) => [...prev, ocrMsg]);
    setPendingOcrDraft(null);
    sendMessage(`I have attached my prescription text: ${ocrFormattedText.slice(0, 120)}...`);
  };

  const resetChat = () => {
    setMessages([]);
    setThreadId('');
    setPendingAction(null);
    setPendingOcrDraft(null);
    setError('');
    try {
      sessionStorage.removeItem(STORAGE_KEY_THREAD);
      sessionStorage.removeItem(STORAGE_KEY_MSGS);
    } catch {}
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        threadId,
        isOpen,
        setIsOpen,
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
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return ctx;
}
