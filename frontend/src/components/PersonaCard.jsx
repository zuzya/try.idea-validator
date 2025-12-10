function PersonaCard({ persona }) {
    return (
        <div className="persona-card glass-card">
            <div className="persona-header">
                <div className="persona-avatar">👤</div>
                <div className="persona-info">
                    <h4>{persona.name}</h4>
                    <span>{persona.role}</span>
                </div>
            </div>

            <p className="persona-bio">{persona.bio}</p>

            {persona.company_context && (
                <p className="persona-bio" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    🏢 {persona.company_context}
                </p>
            )}

            {persona.key_frustrations && persona.key_frustrations.length > 0 && (
                <div className="persona-tags">
                    {persona.key_frustrations.slice(0, 3).map((f, idx) => (
                        <span key={idx} className="persona-tag">😤 {f}</span>
                    ))}
                </div>
            )}

            {persona.tech_stack && persona.tech_stack.length > 0 && (
                <div className="persona-tags" style={{ marginTop: 'var(--space-xs)' }}>
                    {persona.tech_stack.slice(0, 3).map((t, idx) => (
                        <span key={idx} className="persona-tag" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)' }}>
                            💻 {t}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

export default PersonaCard;
