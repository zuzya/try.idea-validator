function PersonaCard({ persona }) {
    return (
        <div className="persona-card" style={{
            background: 'white',
            border: '3px solid black',
            padding: '1rem',
            boxShadow: '4px 4px 0 rgba(0,0,0,0.2)',
            transform: `rotate(${Math.random() * 4 - 2}deg)` // Random slight rotation
        }}>
            <div className="persona-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem', borderBottom: '2px solid black', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                <div className="persona-avatar" style={{
                    fontSize: '2rem',
                    background: '#ccc',
                    borderRadius: '50%',
                    width: '50px',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '2px solid black'
                }}>
                    👤
                </div>
                <div className="persona-info">
                    <h4 style={{ margin: 0, fontFamily: 'var(--font-headline)', fontSize: '1.2rem' }}>{persona.name}</h4>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', textTransform: 'uppercase' }}>{persona.role}</span>
                </div>
            </div>

            <p className="persona-bio" style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', lineHeight: '1.4' }}>
                {persona.bio}
            </p>

            {persona.company_context && (
                <p className="persona-bio" style={{ fontSize: '0.8rem', color: '#666', fontStyle: 'italic', marginTop: '0.5rem' }}>
                    🏢 {persona.company_context}
                </p>
            )}

            <div style={{ marginTop: '1rem' }}>
                {persona.key_frustrations && persona.key_frustrations.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {persona.key_frustrations.slice(0, 3).map((f, idx) => (
                            <span key={idx} className="persona-tag" style={{
                                background: '#FECACA',
                                border: '1px solid black',
                                padding: '2px 6px',
                                fontSize: '0.75rem',
                                fontWeight: 'bold'
                            }}>
                                😤 {f}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default PersonaCard;
