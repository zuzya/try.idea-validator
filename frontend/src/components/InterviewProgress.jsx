function InterviewProgress({ interviews, totalPersonas, isRunning }) {
    const completedCount = interviews.length;
    const progress = totalPersonas > 0 ? (completedCount / totalPersonas) * 100 : 0;

    const getQuestionCount = (interview) => {
        if (!interview?.full_transcript) return 0;
        return (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length;
    };

    return (
        <section className="comic-panel" style={{ background: 'var(--c-panel)' }}>
            <div className="section-card-header" style={{ marginBottom: '1rem', borderBottom: '2px dashed var(--c-ink)', paddingBottom: '0.5rem' }}>
                <h3>
                    <span className="section-icon">🗣️</span>
                    INTERVIEW LOG
                </h3>
            </div>

            <div className="interview-progress">
                {/* Stats Row */}
                <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
                    <div className="interview-stat">
                        <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '1.5rem', color: 'var(--c-ink)' }}>
                            {completedCount}/{totalPersonas}
                        </span>
                        <span className="interview-stat-label">SUBJECTS</span>
                    </div>
                    {interviews.length > 0 && (
                        <div className="interview-stat">
                            <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '1.5rem', color: 'var(--c-danger)' }}>
                                {(interviews.reduce((sum, i) => sum + i.pain_level, 0) / interviews.length).toFixed(1)}
                            </span>
                            <span className="interview-stat-label">AVG PAIN</span>
                        </div>
                    )}
                </div>

                {/* Progress Bar Container */}
                <div className="progress-bar" style={{
                    height: '24px',
                    background: 'var(--c-white)',
                    border: 'var(--border-width) solid var(--c-ink)',
                    borderRadius: '0',
                    position: 'relative',
                    boxShadow: '4px 4px 0 rgba(0,0,0,0.1)'
                }}>
                    <div
                        className="progress-bar-fill"
                        style={{
                            width: `${progress}%`,
                            background: `repeating-linear-gradient(
                              45deg,
                              var(--c-primary),
                              var(--c-primary) 10px,
                              var(--c-primary-hover) 10px,
                              var(--c-primary-hover) 20px
                            )`,
                            height: '100%',
                            transition: 'width 0.5s ease'
                        }}
                    ></div>
                </div>

                {/* Interview List (Compact) */}
                {interviews.length > 0 && (
                    <div className="interview-list" style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {interviews.map((interview, idx) => (
                            <div key={idx} className="interview-item" style={{
                                background: 'var(--c-panel)',
                                border: '1px solid var(--c-ink)',
                                padding: '0.5rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <span>👤</span>
                                    <span style={{ fontWeight: 'bold' }}>{interview.persona.name}</span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <span className="badge" style={{ background: 'var(--c-warning-bg)', color: 'var(--c-warning)', fontSize: '0.8rem', border: '1px solid var(--c-ink)' }}>🔥 {interview.pain_level}</span>
                                    <span className="badge" style={{ background: 'var(--c-success-bg)', color: 'var(--c-success)', fontSize: '0.8rem', border: '1px solid var(--c-ink)' }}>💰 {interview.willingness_to_pay}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {isRunning && (
                    <div className="loading-state" style={{ marginTop: '1rem', fontStyle: 'italic' }}>
                        <span className="loading-spinner"></span>
                        Recording in progress...
                    </div>
                )}
            </div>
        </section>
    );
}

export default InterviewProgress;
