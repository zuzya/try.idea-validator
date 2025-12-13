import ReactMarkdown from 'react-markdown';

function CritiqueCard({ critique }) {
    const getScoreColor = (score) => {
        if (score >= 8) return '#4ADE80'; // Green
        if (score >= 5) return '#FCD34D'; // Yellow
        return '#EF4444'; // Red
    };

    return (
        <div className="comic-panel critique-card" style={{
            border: 'var(--border-width) solid var(--c-ink)',
            transform: 'rotate(1deg)',
            background: 'var(--c-panel)'
        }}>
            <div className="section-card-header" style={{ borderBottom: '2px solid var(--c-ink)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                <h3>
                    <span className="section-icon">🧐</span>
                    INVESTOR MEMO
                </h3>
            </div>

            <div className="critique-content" style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
                <div className="critique-score-wrapper" style={{ flexShrink: 0 }}>
                    <div className="score-display" style={{
                        width: '100px',
                        height: '100px',
                        borderRadius: 'var(--border-radius-comic)',
                        border: 'var(--border-width) solid var(--c-ink)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '3rem',
                        fontWeight: 'bold',
                        color: 'var(--c-ink)',
                        background: getScoreColor(critique.score),
                        boxShadow: 'var(--shadow-comic)'
                    }}>
                        {critique.score}
                    </div>
                </div>

                <div className="critique-details" style={{ flex: 1 }}>
                    {critique.is_approved && (
                        <div className="unicorn-badge" style={{
                            display: 'inline-block',
                            background: 'var(--c-accent)',
                            color: 'white',
                            padding: '0.5rem 1rem',
                            fontSize: '1.2rem',
                            fontWeight: 'bold',
                            marginBottom: '1rem',
                            transform: 'rotate(-2deg)',
                            border: '2px solid var(--c-ink)',
                            boxShadow: '3px 3px 0 var(--c-ink)'
                        }}>
                            🦄 UNICORN POTENTIAL!
                        </div>
                    )}

                    <div className="critique-feedback" style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '1.1rem',
                        position: 'relative',
                        padding: '1rem',
                        background: 'rgba(0,0,0,0.05)',
                        borderLeft: '4px solid var(--c-ink)'
                    }}>
                        <ReactMarkdown>{critique.feedback}</ReactMarkdown>
                        <div style={{
                            position: 'absolute',
                            bottom: '-25px',
                            right: '10px',
                            fontFamily: 'var(--font-marker)',
                            opacity: 1,
                            fontSize: '1.5rem',
                            color: 'var(--c-primary)',
                            transform: 'rotate(-5deg)'
                        }}>
                            - VC PARTNER
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CritiqueCard;
