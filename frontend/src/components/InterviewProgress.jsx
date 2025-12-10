function InterviewProgress({ interviews, totalPersonas, isRunning, activeInterview }) {
    const completedCount = interviews.length;
    const progress = totalPersonas > 0 ? (completedCount / totalPersonas) * 100 : 0;

    // Calculate question count from transcript for each interview
    const getQuestionCount = (interview) => {
        if (!interview?.full_transcript) return 0;
        return (interview.full_transcript.match(/\*\*Interviewer\*\*/g) || []).length;
    };

    return (
        <section className="section-card glass-card fade-in">
            <div className="section-card-header">
                <h3>
                    <span className="section-icon">🗣️</span>
                    Interviews
                </h3>
            </div>

            <div className="interview-progress">
                {/* Overall Stats */}
                <div className="interview-stats">
                    <div className="interview-stat">
                        <span className="interview-stat-value">{completedCount}</span>
                        <span className="interview-stat-label">Completed</span>
                    </div>
                    <div className="interview-stat">
                        <span className="interview-stat-value">{totalPersonas}</span>
                        <span className="interview-stat-label">Total</span>
                    </div>
                    {interviews.length > 0 && (
                        <div className="interview-stat">
                            <span className="interview-stat-value">
                                {(interviews.reduce((sum, i) => sum + i.pain_level, 0) / interviews.length).toFixed(1)}
                            </span>
                            <span className="interview-stat-label">Avg Pain</span>
                        </div>
                    )}
                    {interviews.length > 0 && (
                        <div className="interview-stat">
                            <span className="interview-stat-value">
                                {interviews.reduce((sum, i) => sum + getQuestionCount(i), 0)}
                            </span>
                            <span className="interview-stat-label">Total Questions</span>
                        </div>
                    )}
                </div>

                {/* Overall Progress Bar */}
                <div className="progress-bar">
                    <div
                        className="progress-bar-fill"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>

                {/* Per-Interview Progress */}
                {interviews.length > 0 && (
                    <div className="interview-list">
                        {interviews.map((interview, idx) => {
                            const questionCount = getQuestionCount(interview);
                            return (
                                <div key={idx} className="interview-item">
                                    <div className="interview-item-header">
                                        <span className="interview-item-avatar">👤</span>
                                        <div className="interview-item-info">
                                            <span className="interview-item-name">{interview.persona.name}</span>
                                            <span className="interview-item-role">{interview.persona.role}</span>
                                        </div>
                                        <div className="interview-item-stats">
                                            <span className="badge badge-info">❓ {questionCount}</span>
                                            <span className="badge badge-warning">🔥 {interview.pain_level}/10</span>
                                            <span className="badge badge-success">💰 {interview.willingness_to_pay}/10</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {isRunning && (
                    <div className="loading-state">
                        <span className="loading-spinner"></span>
                        <span>Conducting interviews...</span>
                    </div>
                )}
            </div>
        </section>
    );
}

export default InterviewProgress;
