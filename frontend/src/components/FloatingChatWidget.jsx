import React from 'react';
import { useChat } from '../context/ChatContext';
import ChatWindow from './ChatWindow';
import { MessageSquare, X, Sparkles } from 'lucide-react';

export default function FloatingChatWidget({ onNavigateToFullChat, isFullChatVisible = false }) {
  const { isOpen, setIsOpen, pendingAction } = useChat();

  // Hide the floating button if full chat is already on the screen
  if (isFullChatVisible) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
      }}
    >
      {/* Floating Chat Modal */}
      {isOpen && (
        <div
          style={{
            width: '380px',
            maxWidth: 'calc(100vw - 32px)',
            height: '560px',
            maxHeight: 'calc(100vh - 100px)',
            marginBottom: '14px',
            borderRadius: '24px',
            overflow: 'hidden',
            boxShadow: '0 20px 48px -8px rgba(0, 0, 0, 0.22), 0 0 0 1px rgba(0, 0, 0, 0.08)',
            background: 'var(--surface, #ffffff)',
            animation: 'fadeInUp 0.2s ease-out',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <ChatWindow
            mode="widget"
            onExpand={() => {
              setIsOpen(false);
              if (onNavigateToFullChat) onNavigateToFullChat();
            }}
          />
        </div>
      )}

      {/* Launcher Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '28px',
          border: 'none',
          background: 'linear-gradient(135deg, var(--coral, #FFB7B2), #ffa8a1)',
          color: 'var(--ink, #292524)',
          boxShadow: '0 8px 24px rgba(255, 183, 178, 0.45), 0 2px 6px rgba(0,0,0,0.1)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          transition: 'transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = 'scale(1.06)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
        }}
        title={isOpen ? 'Close chat' : 'Open AI Front Desk'}
        aria-label="Toggle NetraCare AI Front Desk Chat"
      >
        {isOpen ? <X size={22} /> : <MessageSquare size={22} />}

        {/* Action Needed Badge */}
        {!isOpen && pendingAction && (
          <span
            style={{
              position: 'absolute',
              top: '-3px',
              right: '-3px',
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: '#ef4444',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 0 2px #ffffff',
              animation: 'pulse 2s infinite',
            }}
          >
            !
          </span>
        )}
      </button>
    </div>
  );
}
