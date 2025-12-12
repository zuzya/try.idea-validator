function CritiqueCard({ critique }) {
    const getScoreColor = (score) => {
        if (score >= 8) return '#4ADE80'; // Green
        if (score >= 5) return '#FCD34D'; // Yellow
        return '#EF4444'; // Red
    };

    return (
        <div className="comic-panel critique-card" style={{
            border: '4px solid black',
            transform: 'rotate(1deg)',
            background: 'white'
        }}>
            <div className="section-card-header" style={{ borderBottom: '2px solid black', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
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
                        borderRadius: '50%',
                        border: '4px solid black',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '3rem',
                        fontWeight: 'bold',
                        color: 'black',
                        background: getScoreColor(critique.score),
                        boxShadow: '4px 4px 0 rgba(0,0,0,1)'
                    }}>
                        {critique.score}
                    </div>
                </div>

                <div className="critique-details" style={{ flex: 1 }}>
                    {critique.is_approved && (
                        <div className="unicorn-badge" style={{
                            display: 'inline-block',
                            background: 'var(--c-magenta)',
                            color: 'white',
                            padding: '0.5rem 1rem',
                            fontSize: '1.2rem',
                            fontWeight: 'bold',
                            marginBottom: '1rem',
                            transform: 'rotate(-2deg)',
                            border: '2px solid black',
                            boxShadow: '3px 3px 0 black'
                        }}>
                            🦄 UNICORN POTENTIAL!
                        </div>
                    )}

                    <div className="critique-feedback" style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '1.1rem',
                        position: 'relative',
                        padding: '1rem',
                        background: '#eee',
                        borderLeft: '4px solid black'
                    }}>
                        "{critique.feedback}"
                        <div style={{
                            position: 'absolute',
                            bottom: '-10px',
                            right: '10px',
                            fontFamily: 'var(--font-marker)',
                            opacity: 0.3,
                            fontSize: '2rem'
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
