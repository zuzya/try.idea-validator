function IntroPanel() {
    return (
        <div className="intro-panel" style={{
            background: 'var(--c-paper)',
            border: '3px solid var(--c-ink)',
            padding: '1.5rem',
            marginBottom: '2rem',
            boxShadow: '8px 8px 0 rgba(0,0,0,0.1)',
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'baseline',
                borderBottom: '2px solid var(--c-ink)',
                marginBottom: '1rem',
                paddingBottom: '0.5rem',
                justifyContent: 'space-between'
            }}>
                <h3 style={{
                    fontFamily: 'var(--font-headline)',
                    margin: 0,
                    fontSize: '1.8rem'
                }}>
                    📰 EDITOR'S MANUAL
                </h3>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--c-ink-soft)' }}>VOL. 1</span>
            </div>

            <div style={{ fontFamily: 'var(--font-body)', fontSize: '1.1rem', lineHeight: 1.5 }}>
                <p style={{ marginBottom: '1rem' }}><strong>Welcome to the Newsroom!</strong> Validate your startup concept in 4 simple steps:</p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <div style={{ background: '#fff', padding: '1rem', border: '2px solid var(--c-ink)' }}>
                        <div style={{ color: 'var(--c-primary)', fontWeight: 'bold', fontSize: '1.2rem' }}>1. THE PITCH</div>
                        Enter your idea below. Be specific about the problem and solution.
                    </div>

                    <div style={{ background: '#fff', padding: '1rem', border: '2px solid var(--c-ink)' }}>
                        <div style={{ color: 'var(--c-primary)', fontWeight: 'bold', fontSize: '1.2rem' }}>2. SIMULATE</div>
                        We recruit synthetic users and run "Mom Test" interviews.
                    </div>

                    <div style={{ background: '#fff', padding: '1rem', border: '2px solid var(--c-ink)' }}>
                        <div style={{ color: 'var(--c-primary)', fontWeight: 'bold', fontSize: '1.2rem' }}>3. ANALYZE</div>
                        Get a research dossier with confirmed hypotheses and insights.
                    </div>

                    <div style={{ background: '#fff', padding: '1rem', border: '2px solid var(--c-ink)' }}>
                        <div style={{ color: 'var(--c-primary)', fontWeight: 'bold', fontSize: '1.2rem' }}>4. CRITIQUE</div>
                        Face the VC Bot. If you survive, iterate and print the next issue!
                    </div>
                </div>

                <div style={{
                    marginTop: '1.5rem',
                    background: 'var(--c-highlight)',
                    color: 'var(--c-ink)',
                    padding: '0.5rem 1rem',
                    display: 'inline-block',
                    fontFamily: 'var(--font-marker)',
                    transform: 'rotate(-1deg)'
                }}>
                    TIP: Use "Heavy Thinking" for deeper reasoning!
                </div>
            </div>
        </div>
    );
}

export default IntroPanel;
