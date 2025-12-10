function CritiqueCard({ critique }) {
    const getScoreClass = (score) => {
        if (score >= 8) return 'score-high';
        if (score >= 5) return 'score-medium';
        return 'score-low';
    };

    return (
        <section className="section-card glass-card fade-in">
            <div className="section-card-header">
                <h3>
                    <span className="section-icon">🧐</span>
                    Investor Critique
                </h3>
            </div>

            <div className="critique-content">
                <div className="critique-score-wrapper">
                    <div className={`score-display ${getScoreClass(critique.score)}`}>
                        {critique.score}
                    </div>
                </div>

                <div className="critique-details">
                    {critique.is_approved && (
                        <div className="unicorn-badge">
                            🦄 UNICORN DETECTED!
                        </div>
                    )}

                    <p className="critique-feedback">{critique.feedback}</p>
                </div>
            </div>
        </section>
    );
}

export default CritiqueCard;
