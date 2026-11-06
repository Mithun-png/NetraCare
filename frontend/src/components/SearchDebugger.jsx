import React, { useState } from 'react';
import { Search, Database, Layers, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';

export default function SearchDebugger() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const testQueries = [
    "Should I bring my HbA1c report?",
    "Can my kid have breakfast on the morning of the operation to straighten his eye?",
    "What should I avoid after cataract surgery?",
    "When can I swim after LASIK?",
  ];

  const handleSearch = async (qToSearch) => {
    const q = (qToSearch || query).trim();
    if (!q) return;

    setLoading(true);
    setError('');
    try {
      const data = await api.getSearchDebug(q);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Failed to execute search debug.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ display: 'grid', gap: '16px' }}>
      <div>
        <h3 style={{ margin: 0, fontSize: '1.15rem' }}>RAG Search Debugger (BM25 vs Vector vs Hybrid)</h3>
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: '0.88rem' }}>
          Inspect internal ranking from BM25 keyword search, Dense Vector search, and the 50/50 Hybrid retriever.
        </p>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        <span style={{ fontSize: '0.82rem', color: 'var(--muted)', alignSelf: 'center' }}>Test benchmarks:</span>
        {testQueries.map((tq, i) => (
          <button
            key={i}
            onClick={() => {
              setQuery(tq);
              handleSearch(tq);
            }}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '4px 10px' }}
          >
            {tq}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          className="input"
          placeholder="Type any search query to inspect retrieval scores..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          style={{ flex: 1 }}
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading || !query.trim()}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Search size={16} /> Search
        </button>
      </div>

      {error && (
        <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.88rem' }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--muted)' }}>
          Computing BM25 tokens and vector similarities...
        </div>
      )}

      {results && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '8px' }}>
          {/* Keyword Column */}
          <div style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: '10px', padding: '14px', display: 'grid', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--ink)' }}>
              <Layers size={16} color="var(--accent)" /> Keyword Only (BM25)
            </div>
            <div style={{ display: 'grid', gap: '8px' }}>
              {results.keyword.map((item, idx) => (
                <div key={idx} style={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: '6px', padding: '10px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <b style={{ color: 'var(--accent)' }}>#{idx + 1} {item.section}</b>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', background: 'var(--accent-soft)', padding: '2px 6px', borderRadius: '4px' }}>
                      BM25: {item.score}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '4px' }}>
                    {item.source} · <code style={{ fontSize: '0.72rem' }}>{item.chunk_id}</code>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--ink)', lineHeight: '1.4' }}>
                    {item.snippet}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Vector Column */}
          <div style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: '10px', padding: '14px', display: 'grid', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--ink)' }}>
              <Database size={16} color="#7a4a12" /> Vector Only (Cosine Sim)
            </div>
            <div style={{ display: 'grid', gap: '8px' }}>
              {results.vector.map((item, idx) => (
                <div key={idx} style={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: '6px', padding: '10px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <b style={{ color: '#7a4a12' }}>#{idx + 1} {item.section}</b>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', background: 'var(--surgery)', color: 'var(--surgery-ink)', padding: '2px 6px', borderRadius: '4px' }}>
                      Sim: {item.score}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '4px' }}>
                    {item.source} · <code style={{ fontSize: '0.72rem' }}>{item.chunk_id}</code>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--ink)', lineHeight: '1.4' }}>
                    {item.snippet}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hybrid Column */}
          <div style={{ background: 'var(--accent-soft)', border: '2px solid var(--accent)', borderRadius: '10px', padding: '14px', display: 'grid', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--accent)' }}>
              <CheckCircle2 size={16} /> Hybrid (Chat Retriever Top 4)
            </div>
            <div style={{ display: 'grid', gap: '8px' }}>
              {results.hybrid.map((item, idx) => (
                <div key={idx} style={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: '6px', padding: '10px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <b style={{ color: 'var(--accent)' }}>#{idx + 1} {item.section}</b>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', background: 'var(--accent)', color: '#fff', padding: '2px 6px', borderRadius: '4px' }}>
                      Hybrid: {item.score}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '4px' }}>
                    {item.source} · <code style={{ fontSize: '0.72rem' }}>{item.chunk_id}</code>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--ink)', lineHeight: '1.4' }}>
                    {item.snippet}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

