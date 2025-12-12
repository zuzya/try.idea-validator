function AnalystReport({ report }) {
    return (
        <div className="comic-panel analyst-report" style={{
            background: '#fcfbf9',
            backgroundImage: 'repeating-linear-gradient(#fcfbf9 0px, #fcfbf9 24px, #e8e4dc 25px)',
            lineHeight: '25px',
            position: 'relative'
        }}>
            {/* Paperclip visual could go here via CSS/SVG */}
            <div style={{
                position: 'absolute',
                top: '-20px',
                right: '20px',
                background: '#ffcc00',
                padding: '0.5rem 1rem',
                border: '2px solid black',
                transform: 'rotate(3deg)',
                fontFamily: 'var(--font-marker)',
                boxShadow: '2px 2px 0 rgba(0,0,0,0.2)'
            }}>
                CONFIDENTIAL
            </div>

            <h3 style={{ textDecoration: 'underline', marginBottom: '1.5rem' }}>
                <span className="section-icon">📊</span> ANALYST DOSSIER
            </h3>

            <div className="report-content">
                {/* Pivot Recommendation */}
                <div className="report-recommendation" style={{
                    border: '3px solid black',
                    padding: '1rem',
                    background: 'white',
                    fontFamily: 'var(--font-body)',
                    marginBottom: '1.5rem'
                }}>
                    <strong style={{ background: 'black', color: 'white', padding: '0 5px' }}>RECOMMENDATION:</strong>
                    <p style={{ marginTop: '0.5rem', fontSize: '1.2rem', fontWeight: 'bold' }}>{report.pivot_recommendation}</p>
                </div>

                {/* Hypotheses */}
                <div className="report-columns" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div className="report-column">
                        <h4 style={{ background: '#4ADE80', display: 'inline-block', padding: '2px 5px', border: '2px solid black' }}>
                            ✅ VERIFIED FACTS
                        </h4>
                        <ul className="report-list" style={{ listStyle: 'none', padding: 0 }}>
                            {report.confirmed_hypotheses.map((h, idx) => (
                                <li key={idx} style={{ padding: '0.5rem 0', borderBottom: '1px dashed #ccc' }}>• {h}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="report-column">
                        <h4 style={{ background: '#F87171', display: 'inline-block', padding: '2px 5px', border: '2px solid black' }}>
                            ❌ DEBUNKED MYTHS
                        </h4>
                        <ul className="report-list" style={{ listStyle: 'none', padding: 0 }}>
                            {report.rejected_hypotheses.map((h, idx) => (
                                <li key={idx} style={{ padding: '0.5rem 0', borderBottom: '1px dashed #ccc' }}>• {h}</li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Key Insights */}
                <div style={{ marginTop: '1.5rem' }}>
                    <h4 style={{ color: 'var(--c-text)', marginBottom: '1rem' }}>
                        💡 FIELD NOTES
                    </h4>
                    <div className="insights-list">
                        {report.key_insights.map((insight, idx) => (
                            <div key={idx} className="insight-item" style={{
                                padding: '0.5rem',
                                background: 'rgba(255,255,0,0.2)',
                                marginBottom: '0.5rem',
                                borderLeft: '4px solid black'
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
