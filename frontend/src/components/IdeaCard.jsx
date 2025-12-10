function IdeaCard({ idea, iteration }) {
    return (
        <section className="section-card glass-card fade-in">
            <div className="section-card-header">
                <h3>
                    <span className="section-icon">💡</span>
                    Generated Idea
                    <span className="badge badge-info" style={{ marginLeft: 'var(--space-sm)' }}>
                        Iteration {iteration}
                    </span>
                </h3>
            </div>

            <div className="idea-card">
                <h4 className="idea-title">{idea.title}</h4>
                <p className="idea-description">{idea.description}</p>

                <div className="idea-meta">
                    <div className="idea-meta-item">
                        <span className="idea-meta-label">💰 Monetization</span>
                        <span className="idea-meta-value">{idea.monetization_strategy}</span>
                    </div>
                    <div className="idea-meta-item">
                        <span className="idea-meta-label">🎯 Target Audience</span>
                        <span className="idea-meta-value">{idea.target_audience}</span>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default IdeaCard;
