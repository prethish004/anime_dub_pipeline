import React, { useState, useEffect } from 'react';
import { Target, RefreshCw, Loader2 } from 'lucide-react';
import { getStyleAccuracy } from '../services/api';

const STYLE_ORDER = ['tsundere', 'aggressive', 'formal_cool', 'cute', 'reflective', 'neutral'];

function AccuracyStat({ label, accuracy, correct, total, accent }) {
  return (
    <div className="style-stat" style={{ '--stat-accent': `var(--accent-${accent})` }}>
      <span className="style-stat-label">{label}</span>
      <span className="style-stat-value">{Math.round(accuracy * 100)}%</span>
      <span className="style-stat-sub">{correct} / {total} correct</span>
    </div>
  );
}

function ConfusionMatrix({ matrix }) {
  return (
    <div className="confusion-matrix-wrap">
      <table className="confusion-matrix">
        <thead>
          <tr>
            <th>expected \ got</th>
            {STYLE_ORDER.map((s) => <th key={s}>{s}</th>)}
          </tr>
        </thead>
        <tbody>
          {STYLE_ORDER.map((expected) => (
            <tr key={expected}>
              <th>{expected}</th>
              {STYLE_ORDER.map((predicted) => {
                const count = matrix?.[expected]?.[predicted] || 0;
                const isDiagonal = expected === predicted;
                return (
                  <td key={predicted} className={isDiagonal ? 'diag' : count > 0 ? 'off-diag-hit' : ''}>
                    {count > 0 ? count : ''}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StyleAccuracyPanel() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [matrixMethod, setMatrixMethod] = useState('hybrid');
  const [error, setError] = useState(null);

  const fetchReport = async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStyleAccuracy(refresh);
      setReport(data);
    } catch (e) {
      setError(e.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport(false);
  }, []);

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={20} style={{ color: 'var(--accent-amber)' }} />
          Style Detection Accuracy
        </span>
        <button className="btn btn-secondary" onClick={() => fetchReport(true)} disabled={loading}>
          {loading ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />} Re-run
        </button>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
        Measured against 26 hand-labeled Japanese lines (tsundere, aggressive, formal, cute,
        reflective, neutral) — comparing the old keyword-only matcher against the current
        keyword+classifier hybrid used in Step 3, so the number below is a real measurement,
        not a guess.
      </p>

      {error && <p style={{ color: 'var(--accent-pink)', fontSize: '13px' }}>Error: {error}</p>}

      {report && (
        <>
          <div className="style-stats-row">
            <AccuracyStat
              label="Keyword-only (old)"
              accuracy={report.keyword_only.accuracy}
              correct={report.keyword_only.correct}
              total={report.keyword_only.total}
              accent="cyan"
            />
            <AccuracyStat
              label="Hybrid (current)"
              accuracy={report.hybrid.accuracy}
              correct={report.hybrid.correct}
              total={report.hybrid.total}
              accent="violet"
            />
          </div>

          <div className="style-category-row">
            {['keyword_pattern', 'novel_phrasing'].map((cat) => {
              const kw = report.keyword_only.by_category[cat];
              const hy = report.hybrid.by_category[cat];
              if (!kw && !hy) return null;
              return (
                <div key={cat} className="style-category-card">
                  <span className="style-category-title">
                    {cat === 'keyword_pattern' ? 'Lines using known keywords' : 'Novel phrasing (no keyword overlap)'}
                  </span>
                  <span className="style-category-compare">
                    keyword-only: <b>{Math.round((kw?.accuracy || 0) * 100)}%</b>
                    {'  ->  '}
                    hybrid: <b>{Math.round((hy?.accuracy || 0) * 100)}%</b>
                  </span>
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: '18px' }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              <button
                className={`btn ${matrixMethod === 'hybrid' ? 'btn-secondary active' : 'btn-secondary'}`}
                onClick={() => setMatrixMethod('hybrid')}
              >
                Hybrid confusion matrix
              </button>
              <button
                className={`btn ${matrixMethod === 'keyword_only' ? 'btn-secondary active' : 'btn-secondary'}`}
                onClick={() => setMatrixMethod('keyword_only')}
              >
                Keyword-only confusion matrix
              </button>
            </div>
            <ConfusionMatrix matrix={report[matrixMethod].confusion_matrix} />
          </div>

          {report[matrixMethod].mistakes.length > 0 && (
            <div style={{ marginTop: '18px' }}>
              <span className="style-category-title">Sample mismatches ({matrixMethod.replace('_', ' ')})</span>
              <div className="style-mistakes-list">
                {report[matrixMethod].mistakes.map((m, i) => (
                  <div key={i} className="style-mistake-row">
                    <span className="style-mistake-text">{m.text}</span>
                    <span className="style-mistake-labels">
                      expected <b>{m.expected}</b> &rarr; got <b>{m.got}</b>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '14px', fontFamily: 'var(--font-mono)' }}>
            generated {new Date(report.generated_at).toLocaleString()} · classifier loaded: {String(report.classifier_loaded)}
          </p>
        </>
      )}
    </div>
  );
}
