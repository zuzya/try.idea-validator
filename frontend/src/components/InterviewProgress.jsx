function InterviewProgress({ interviews, totalPersonas, isRunning }) {
    const completedCount = interviews.length;
    const progress = totalPersonas > 0 ? (completedCount / totalPersonas) * 100 : 0;

    const getQuestionCount = (interview) => {
        if (!interview?.full_transcript) return 0;
        return (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length;
    };

    return (
        <section className="comic-panel" style={{ background: '#E0F2FE' }}>
            <div className="section-card-header" style={{ marginBottom: '1rem', borderBottom: '2px dashed black', paddingBottom: '0.5rem' }}>
                <h3>
                    <span className="section-icon">🗣️</span>
                    INTERVIEW LOG
                </h3>
            </div>

            <div className="interview-progress">
                {/* Stats Row */}
                <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
                    <div className="interview-stat">
                        <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '1.5rem' }}>
                            {completedCount}/{totalPersonas}
                        </span>
                        <span className="interview-stat-label">SUBJECTS</span>
                    </div>
                    {interviews.length > 0 && (
                        <div className="interview-stat">
                            <span className="interview-stat-value" style={{ fontFamily: 'var(--font-headline)', fontSize: '1.5rem', color: '#EF4444' }}>
                                {(interviews.reduce((sum, i) => sum + i.pain_level, 0) / interviews.length).toFixed(1)}
                            </span>
                            <span className="interview-stat-label">AVG PAIN</span>
                        </div>
                    )}
                </div>

                {/* Progress Bar Container */}
                <div className="progress-bar" style={{
                    height: '20px',
                    background: 'white',
                    border: '2px solid black',
                    borderRadius: '0',
                    position: 'relative'
                }}>
                    <div
                        className="progress-bar-fill"
                        style={{
                            width: `${progress}%`,
                            background: `repeating-linear-gradient(
                              45deg,
                              var(--c-cyan),
                              var(--c-cyan) 10px,
                              #0ea5e9 10px,
                              #0ea5e9 20px
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
                                background: 'white',
                                border: '1px solid black',
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
                                    <span className="badge" style={{ background: '#FCD34D', fontSize: '0.8rem' }}>🔥 {interview.pain_level}</span>
                                    <span className="badge" style={{ background: '#4ADE80', fontSize: '0.8rem' }}>💰 {interview.willingness_to_pay}</span>
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
