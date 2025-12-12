function IdeaCard({ idea, iteration }) {
    return (
        <div className="comic-panel idea-card" style={{ transform: 'rotate(-1deg)' }}>
            <div style={{
                background: 'var(--c-black)',
                color: 'white',
                padding: '0.2rem 1rem',
                display: 'inline-block',
                position: 'absolute',
                top: '-15px',
                left: '20px',
                transform: 'skew(-10deg)',
                fontFamily: 'var(--font-headline)',
                fontSize: '1.2rem',
                zIndex: 2
            }}>
                THE CONCEPT {iteration && `#${iteration}`}
            </div>

            <h3 className="idea-title" style={{ fontSize: '2rem', marginTop: '0.5rem', marginBottom: '1rem', lineHeight: '1.1' }}>
                {idea.title}
            </h3>

            <div className="idea-description" style={{
                fontFamily: 'var(--font-body)',
                fontSize: '1.1rem',
                lineHeight: '1.5',
                padding: '1rem',
                background: 'var(--c-paper-dim)',
                border: '1px solid black'
            }}>
                {idea.description}
            </div>

            <div className="idea-meta" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div className="idea-meta-item">
                    <span className="badge" style={{ background: 'var(--c-cyan)', color: 'white', marginRight: '0.5rem' }}>TARGET</span>
                    <span style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold' }}>{idea.target_audience}</span>
                </div>
                <div className="idea-meta-item">
                    <span className="badge" style={{ background: 'var(--c-magenta)', color: 'white', marginRight: '0.5rem' }}>MONEY</span>
                    <span style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold' }}>{idea.monetization_strategy}</span>
                </div>
            </div>
        </div>
    );
}

export default IdeaCard;
