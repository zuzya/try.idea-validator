import ReactMarkdown from 'react-markdown';

function TranscriptModal({ interview, onClose }) {
  // Count questions in transcript (lines starting with **Interviewer**)
  const questionCount = interview.full_transcript
    ? (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length
    : 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <span>📜</span>
            {interview.persona.name} — Interview Transcript
          </h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Summary */}
          <div style={{ marginBottom: 'var(--space-lg)' }}>
            <h4 style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-sm)' }}>
              📝 Summary
            </h4>
            <div className="insight-item">
              {interview.transcript_summary}
            </div>
          </div>

          {/* Scores */}
          <div style={{ display: 'flex', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
            <div className="interview-stat">
              <span className="interview-stat-value">🔥 {interview.pain_level}/10</span>
              <span className="interview-stat-label">Pain Level</span>
            </div>
            <div className="interview-stat">
              <span className="interview-stat-value">💰 {interview.willingness_to_pay}/10</span>
              <span className="interview-stat-label">Willingness to Pay</span>
            </div>
            {questionCount > 0 && (
              <div className="interview-stat">
                <span className="interview-stat-value">❓ {questionCount}</span>
                <span className="interview-stat-label">Questions Asked</span>
              </div>
            )}
          </div>

          {/* Full Transcript (Markdown) */}
          {interview.full_transcript && (
            <div>
              <h4 style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-sm)' }}>
                💬 Full Transcript
              </h4>
              <div className="transcript-markdown">
                <ReactMarkdown>{interview.full_transcript}</ReactMarkdown>
              </div>
            </div>
          )}

          {!interview.full_transcript && (
            <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Full transcript not available for this interview.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default TranscriptModal;
