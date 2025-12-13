import ReactMarkdown from 'react-markdown';

function TranscriptModal({ interview, onClose }) {
  // Count questions in transcript (lines starting with **Interviewer**)
  const questionCount = interview.full_transcript
    ? (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length
    : 0;

  return (
    <div className="modal-overlay" onClick={onClose} style={{
      background: 'rgba(0,0,0,0.5)',
      backdropFilter: 'blur(2px)'
    }}>
      <div className="modal-content fade-in" onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--c-paper)',
        maxWidth: '800px',
        border: 'var(--border-width) solid var(--c-ink)',
        borderRadius: '0',
        boxShadow: 'var(--shadow-deep)'
      }}>
        <div className="modal-header" style={{ background: 'var(--c-ink)', color: 'var(--c-panel)', borderBottom: 'none', padding: '1rem' }}>
          <h3 style={{ margin: 0, fontFamily: 'var(--font-headline)', color: 'var(--c-panel)', textShadow: 'none' }}>
            <span>📜</span> TRANSCRIPT: {interview.persona.name.toUpperCase()}
          </h3>
          <button className="modal-close" onClick={onClose} style={{ color: 'var(--c-panel)', fontSize: '2rem', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
        </div>

        <div className="modal-body" style={{ background: 'var(--c-paper)', padding: '2rem' }}>
          {/* Summary */}
          <div style={{
            marginBottom: '2rem',
            border: '2px solid var(--c-ink)',
            padding: '1rem',
            background: 'var(--c-paper-2)'
          }}>
            <h4 style={{ margin: '0 0 0.5rem 0', textTransform: 'uppercase', fontSize: '0.9rem', fontFamily: 'var(--font-headline)' }}>
              📝 Executive Summary
            </h4>
            <div style={{ fontFamily: 'var(--font-body)' }}>
              {interview.transcript_summary}
            </div>
          </div>

          {/* Scores */}
          <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', borderBottom: '2px dashed var(--c-ink)', paddingBottom: '1rem' }}>
            <div className="interview-stat">
              <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '2rem', color: 'var(--c-ink)' }}>{interview.pain_level}/10</span>
              <span className="interview-stat-label" style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold' }}>PAIN LEVEL</span>
            </div>
            <div className="interview-stat">
              <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '2rem', color: 'var(--c-ink)' }}>{interview.willingness_to_pay}/10</span>
              <span className="interview-stat-label" style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold' }}>WTP</span>
            </div>
          </div>

          {/* Full Transcript (Markdown) */}
          {interview.full_transcript && (
            <div>
              <h4 style={{ marginBottom: '1rem', fontFamily: 'var(--font-headline)' }}>
                💬 RECORDED CONVERSATION
              </h4>
              <div className="transcript-markdown" style={{
                fontFamily: 'Courier Prime, monospace',
                fontSize: '1rem',
                lineHeight: '1.4',
                background: 'var(--c-panel)',
                border: 'var(--border-width) solid var(--c-ink)',
                padding: '1rem'
              }}>
                <ReactMarkdown>{interview.full_transcript}</ReactMarkdown>
              </div>
            </div>
          )}

          {!interview.full_transcript && (
            <p style={{ fontStyle: 'italic', opacity: 0.7 }}>
              [Tape corrupted. No transcript available.]
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default TranscriptModal;
