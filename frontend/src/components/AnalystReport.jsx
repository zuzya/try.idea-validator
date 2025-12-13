function AnalystReport({ report }) {
    return (
        <div className="comic-panel analyst-report" style={{
            background: 'var(--c-paper)',
            backgroundImage: 'repeating-linear-gradient(var(--c-paper) 0px, var(--c-paper) 24px, #e8e4dc 25px)',
            lineHeight: '25px',
            position: 'relative',
            border: 'var(--border-width) solid var(--c-ink)'
        }}>
            {/* Paperclip visual */}
            <div style={{
                position: 'absolute',
                top: '-20px',
                right: '20px',
                background: 'var(--c-ink)',
                color: 'var(--c-panel)',
                padding: '0.5rem 1rem',
                border: '2px solid var(--c-panel)',
                transform: 'rotate(3deg)',
                fontFamily: 'var(--font-marker)',
                boxShadow: '4px 4px 0 rgba(0,0,0,0.2)',
                outline: '2px solid var(--c-ink)'
            }}>
                CONFIDENTIAL
            </div>

            <h3 style={{ textDecoration: 'underline', marginBottom: '1.5rem', fontFamily: 'var(--font-headline)' }}>
                <span className="section-icon">📊</span> ANALYST DOSSIER
            </h3>

            <div className="report-content">
                {/* Pivot Recommendation */}
                <div className="report-recommendation" style={{
                    border: 'var(--border-width) solid var(--c-ink)',
                    padding: '1rem',
                    background: 'var(--c-panel)',
                    color: 'var(--c-ink)',
                    fontFamily: 'var(--font-body)',
                    marginBottom: '1.5rem'
                }}>
                    <strong style={{ background: 'var(--c-ink)', color: 'var(--c-panel)', padding: '0 5px' }}>RECOMMENDATION:</strong>
                    <p style={{ marginTop: '0.5rem', fontSize: '1.2rem', fontWeight: 'bold' }}>{report.pivot_recommendation}</p>
                </div>

                {/* Hypotheses */}
                <div className="report-columns" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div className="report-column">
                        <h4 style={{ background: 'var(--c-success)', color: 'var(--c-panel)', display: 'inline-block', padding: '2px 5px', border: '2px solid var(--c-ink)' }}>
                            ✅ VERIFIED FACTS
                        </h4>
                        <ul className="report-list" style={{ listStyle: 'none', padding: 0 }}>
                            {report.confirmed_hypotheses.map((h, idx) => (
                                <li key={idx} style={{ padding: '0.5rem 0', borderBottom: '2px dashed var(--c-muted)' }}>• {h}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="report-column">
                        <h4 style={{ background: 'var(--c-primary)', color: 'var(--c-panel)', display: 'inline-block', padding: '2px 5px', border: '2px solid var(--c-ink)' }}>
                            ❌ DEBUNKED MYTHS
                        </h4>
                        <ul className="report-list" style={{ listStyle: 'none', padding: 0 }}>
                            {report.rejected_hypotheses.map((h, idx) => (
                                <li key={idx} style={{ padding: '0.5rem 0', borderBottom: '2px dashed var(--c-muted)' }}>• {h}</li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Key Insights */}
                <div style={{ marginTop: '1.5rem' }}>
                    <h4 style={{ color: 'var(--c-ink)', marginBottom: '1rem' }}>
                        💡 FIELD NOTES
                    </h4>
                    <div className="insights-list">
                        {report.key_insights.map((insight, idx) => (
                            <div key={idx} className="insight-item" style={{
                                padding: '0.5rem',
                                background: 'rgba(0,0,0,0.05)',
                                marginBottom: '0.5rem',
                                borderLeft: '8px solid var(--c-highlight)'
                            }}>
                                <span>{insight}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AnalystReport;
