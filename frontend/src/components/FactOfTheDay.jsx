import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sparkles, RefreshCw } from 'lucide-react';

export default function FactOfTheDay() {
  const [fact, setFact] = useState('');
  const [caveat, setCaveat] = useState('General information, not medical advice');
  const [loading, setLoading] = useState(false);

  const fetchFact = async (previousFact = null) => {
    setLoading(true);
    try {
      const res = await api.getFactOfTheDay(previousFact);
      if (res.ok) {
        setFact(res.fact);
        setCaveat(res.caveat || 'General information, not medical advice');
      }
    } catch (e) {
      console.error(e);
      if (!fact) {
        setFact("Human corneas receive oxygen directly through tears and the air rather than blood vessels.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFact();
  }, []);

  const handleRefresh = () => {
    fetchFact(fact);
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #ffffff 0%, var(--accent-soft) 100%)',
      border: '1px solid var(--line)',
      borderRadius: '12px',
      padding: '16px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{
          background: 'var(--accent)',
          color: '#ffffff',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: '2px',
        }}>
          <Sparkles size={16} />
        </div>
        <div>
          <span style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--accent)',
          }}>
            Fact of the Day
          </span>
          <p style={{
            fontSize: '0.98rem',
            color: 'var(--ink)',
            marginTop: '2px',
            marginBottom: '4px',
            maxWidth: '680px',
            lineHeight: 1.45,
          }}>
            {fact || "Loading eye health fact..."}
          </p>
          <span style={{ fontSize: '0.78rem', color: 'var(--muted)', fontStyle: 'italic' }}>
            {caveat}
          </span>
        </div>
      </div>

      <button
        type="button"
        className="btn btn-secondary"
        style={{
          padding: '6px 12px',
          fontSize: '0.85rem',
          flexShrink: 0,
        }}
        onClick={handleRefresh}
        disabled={loading}
      >
        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        {loading ? 'Fetching...' : 'Refresh'}
      </button>
    </div>
  );
}
