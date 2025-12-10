function AnalystReport({ report }) {
    return (
        <section className="section-card glass-card fade-in">
            <div className="section-card-header">
                <h3>
                    <span className="section-icon">📊</span>
                    Analyst Report
                </h3>
            </div>

            <div className="report-content">
                {/* Pivot Recommendation */}
                <div className="report-recommendation">
                    <strong>🔄 Pivot Recommendation:</strong>
                    <p style={{ marginTop: 'var(--space-sm)' }}>{report.pivot_recommendation}</p>
                </div>

                {/* Hypotheses */}
                <div className="report-columns">
                    <div className="report-column">
                        <h4>✅ Confirmed Hypotheses</h4>
                        <ul className="report-list">
                            {report.confirmed_hypotheses.map((h, idx) => (
                                <li key={idx}>{h}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="report-column">
                        <h4>❌ Rejected Hypotheses</h4>
                        <ul className="report-list">
                            {report.rejected_hypotheses.map((h, idx) => (
                                <li key={idx}>{h}</li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Key Insights */}
                <div>
                    <h4 style={{ marginBottom: 'var(--space-sm)', color: 'var(--text-secondary)' }}>
                        💡 Key Insights
                    </h4>
                    <div className="insights-list">
                        {report.key_insights.map((insight, idx) => (
                            <div key={idx} className="insight-item">
                                <span className="insight-icon">💡</span>
                                <span>{insight}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

export default AnalystReport;
