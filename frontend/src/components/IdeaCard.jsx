function IdeaCard({ idea, iteration }) {
    return (
        <div className="comic-panel idea-card" style={{
            transform: 'rotate(0deg)',
            border: 'var(--border-width) solid var(--c-ink)',
            boxShadow: '8px 8px 0 var(--c-ink)',
            background: 'var(--c-panel)',
            position: 'relative'
        }}>
            <div style={{
                background: 'var(--c-primary)',
                color: 'var(--c-panel)',
                padding: '0.2rem 1rem',
                display: 'inline-block',
                position: 'absolute',
                top: '-15px',
                left: '-4px',
                fontFamily: 'var(--font-headline)',
                fontSize: '1.4rem',
                zIndex: 2,
                border: 'var(--border-width) solid var(--c-ink)'
            }}>
                THE CONCEPT {iteration && `#${iteration}`}
            </div>

            <h3 className="idea-title" style={{ fontSize: '2rem', marginTop: '1rem', marginBottom: '1rem', lineHeight: '1.1', textTransform: 'uppercase', color: 'var(--c-ink)' }}>
                {idea.title}
            </h3>

            <div className="idea-description" style={{
                fontFamily: 'var(--font-body)',
                fontSize: '1.1rem',
                lineHeight: '1.5',
                padding: '1rem',
                background: 'rgba(0,0,0,0.03)', /* Subtle darkening */
                borderLeft: '6px solid var(--c-primary)',
                color: 'var(--c-ink-soft)'
            }}>
                {idea.description}
            </div>

            <div className="idea-meta" style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div className="idea-meta-item">
                    <span className="badge" style={{ background: 'var(--c-ink)', color: 'var(--c-panel)', marginRight: '0.5rem', border: 'none' }}>TARGET</span>
                    <span style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold', color: 'var(--c-ink)' }}>{idea.target_audience}</span>
                </div>
                <div className="idea-meta-item">
                    <span className="badge" style={{ background: 'var(--c-ink)', color: 'var(--c-panel)', marginRight: '0.5rem', border: 'none' }}>MONEY</span>
                    <span style={{ fontFamily: 'var(--font-body)', fontWeight: 'bold', color: 'var(--c-ink)' }}>{idea.monetization_strategy}</span>
                </div>
            </div>
        </div>
    );
}

export default IdeaCard;
