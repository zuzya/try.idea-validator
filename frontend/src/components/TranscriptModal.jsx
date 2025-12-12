import ReactMarkdown from 'react-markdown';

function TranscriptModal({ interview, onClose }) {
  // Count questions in transcript (lines starting with **Interviewer**)
  const questionCount = interview.full_transcript
    ? (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length
    : 0;

  return (
    <div className="modal-overlay" onClick={onClose} style={{
      background: 'rgba(0,0,0,0.85)',
      backdropFilter: 'grayscale(100%) blur(2px)' // Film noir vibe
    }}>
      <div className="modal-content fade-in" onClick={(e) => e.stopPropagation()} style={{
        background: '#fff',
        maxWidth: '800px',
        border: '4px solid black',
        borderRadius: '0',
        boxShadow: '10px 10px 0 rgba(255,255,255,0.2)'
      }}>
        <div className="modal-header" style={{ background: 'black', color: 'white', borderBottom: 'none' }}>
          <h3 style={{ margin: 0, fontFamily: 'var(--font-headline)', color: 'white', textShadow: 'none' }}>
            <span>📜</span> TRANSCRIPT: {interview.persona.name.toUpperCase()}
          </h3>
          <button className="modal-close" onClick={onClose} style={{ color: 'white', fontSize: '2rem' }}>×</button>
        </div>

        <div className="modal-body" style={{ background: '#fcfbf9' }}>
          {/* Summary */}
          <div style={{
            marginBottom: '2rem',
            border: '2px solid black',
            padding: '1rem',
            background: '#e5e7eb'
          }}>
            <h4 style={{ margin: '0 0 0.5rem 0', textTransform: 'uppercase', fontSize: '0.9rem' }}>
              📝 Executive Summary
            </h4>
            <div style={{ fontFamily: 'var(--font-body)' }}>
              {interview.transcript_summary}
            </div>
          </div>

          {/* Scores */}
          <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', borderBottom: '2px dashed black', paddingBottom: '1rem' }}>
            <div className="interview-stat">
              <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '2rem' }}>{interview.pain_level}/10</span>
              <span className="interview-stat-label">PAIN LEVEL</span>
            </div>
            <div className="interview-stat">
              <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '2rem' }}>{interview.willingness_to_pay}/10</span>
              <span className="interview-stat-label">WTP</span>
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
                background: 'white',
                border: 'none',
                padding: '0'
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
