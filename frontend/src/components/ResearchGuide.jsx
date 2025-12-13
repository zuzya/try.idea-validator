function ResearchGuide({ guide }) {
    if (!guide) return null;

    return (
        <div className="research-guide" style={{
            background: '#fff',
            border: '2px solid var(--c-ink)',
            padding: '1.5rem',
            marginBottom: '2rem',
            boxShadow: '4px 4px 0 rgba(0,0,0,0.1)',
            transform: 'rotate(-1deg)',
            position: 'relative'
        }}>
            {/* Paper Clip Visual */}
            <div style={{
                position: 'absolute',
                top: '-15px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '60px',
                height: '20px',
                background: '#ccc',
                border: '2px solid var(--c-ink)',
                borderRadius: '10px'
            }}></div>

            <h3 style={{
                fontFamily: 'var(--font-headline)',
                fontSize: '1.5rem',
                borderBottom: '2px dashed var(--c-ink)',
                paddingBottom: '0.5rem',
                marginTop: '0.5rem',
                marginBottom: '1rem'
            }}>
                🕵️ RESEARCH OBJECTIVES
            </h3>

            <div className="guide-content" style={{ display: 'grid', gap: '2rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>

                {/* HYPOTHESES */}
                <div className="guide-section">
                    <h4 style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold', textDecoration: 'underline', marginBottom: '0.5rem' }}>
                        HYPOTHESES TO VERIFY:
                    </h4>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontFamily: 'var(--font-body)' }}>
                        {guide.hypotheses.map((h, idx) => (
                            <li key={idx} style={{ marginBottom: '0.8rem', paddingLeft: '1.5rem', position: 'relative' }}>
                                <span style={{ position: 'absolute', left: 0, color: 'var(--c-primary)', fontWeight: 'bold' }}>?</span>
                                <strong>[{h.type}]</strong> {h.description}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* QUESTIONS */}
                <div className="guide-section">
                    <h4 style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold', textDecoration: 'underline', marginBottom: '0.5rem' }}>
                        INTERVIEW SCRIPT:
                    </h4>
                    <ol style={{ paddingLeft: '1.5rem', margin: 0, fontFamily: 'var(--font-body)' }}>
                        {guide.questions.map((q, idx) => (
                            <li key={idx} style={{ marginBottom: '0.5rem' }}>
                                {q}
                            </li>
                        ))}
                    </ol>
                </div>
            </div>

            {/* Stamp */}
            <div style={{
                position: 'absolute',
                bottom: '10px',
                right: '20px',
                fontFamily: 'var(--font-marker)',
                color: 'var(--c-ink-soft)',
                opacity: 0.2,
                fontSize: '2rem',
                transform: 'rotate(-15deg)',
                border: '3px solid currentColor',
                padding: '0.2rem 1rem'
            }}>
                TOP SECRET
            </div>
        </div>
    );
}

export default ResearchGuide;
