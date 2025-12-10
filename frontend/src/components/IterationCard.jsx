import { useState } from 'react';
import IdeaCard from './IdeaCard';
import PersonaCard from './PersonaCard';
import InterviewProgress from './InterviewProgress';
import AnalystReport from './AnalystReport';
import CritiqueCard from './CritiqueCard';

function IterationCard({ iteration, isActive, onTranscriptClick, config }) {
    const [isExpanded, setIsExpanded] = useState(isActive);

    const {
        number,
        idea,
        recruitedPersonas,
        interviews,
        analystReport,
        critique,
    } = iteration;

    const getStatusBadge = () => {
        if (critique?.is_approved) {
            return <span className="badge badge-success">🦄 APPROVED</span>;
        }
        if (critique) {
            return <span className="badge badge-warning">Score: {critique.score}/10</span>;
        }
        if (isActive) {
            return <span className="badge badge-info pulse">In Progress</span>;
        }
        return null;
    };

    return (
        <div className={`iteration-card ${isActive ? 'active' : ''}`}>
            <div
                className="iteration-header"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="iteration-header-left">
                    <span className={`iteration-arrow ${isExpanded ? 'open' : ''}`}>▼</span>
                    <h3 className="iteration-title">
                        Iteration {number}
                        {idea && <span className="iteration-idea-title">: {idea.title}</span>}
                    </h3>
                </div>
                <div className="iteration-header-right">
                    {getStatusBadge()}
                </div>
            </div>

            {isExpanded && (
                <div className="iteration-content fade-in">
                    {/* Idea */}
                    {idea && (
                        <div className="iteration-section">
                            <IdeaCard idea={idea} iteration={number} />
                        </div>
                    )}

                    {/* Recruited Personas */}
                    {recruitedPersonas && recruitedPersonas.length > 0 && (
                        <div className="iteration-section">
                            <section className="section-card glass-card">
                                <div className="section-card-header">
                                    <h3><span className="section-icon">🕵️</span> Recruited Personas</h3>
                                </div>
                                <div className="persona-grid">
                                    {recruitedPersonas.map((persona, idx) => (
                                        <PersonaCard key={idx} persona={persona} />
                                    ))}
                                </div>
                            </section>
                        </div>
                    )}

                    {/* Interview Progress - show when interviews exist OR when active and personas recruited */}
                    {((interviews && interviews.length > 0) || (isActive && recruitedPersonas && recruitedPersonas.length > 0)) && (
                        <div className="iteration-section">
                            <InterviewProgress
                                interviews={interviews || []}
                                totalPersonas={config?.numPersonas || recruitedPersonas?.length || 3}
                                isRunning={isActive && (!interviews || interviews.length < (config?.numPersonas || 3))}
                            />
                        </div>
                    )}

                    {/* Analyst Report */}
                    {analystReport && (
                        <div className="iteration-section">
                            <AnalystReport report={analystReport} />
                        </div>
                    )}

                    {/* Critique */}
                    {critique && (
                        <div className="iteration-section">
                            <CritiqueCard critique={critique} />
                        </div>
                    )}

                    {/* Interview Transcripts */}
                    {interviews && interviews.length > 0 && (
                        <div className="iteration-section">
                            <section className="section-card glass-card transcript-section">
                                <div className="section-card-header">
                                    <h3><span className="section-icon">📜</span> Interview Transcripts</h3>
                                </div>
                                <div className="transcript-list">
                                    {interviews.map((interview, idx) => (
                                        <div
                                            key={idx}
                                            className="transcript-item"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onTranscriptClick(interview);
                                            }}
                                        >
                                            <div className="transcript-item-info">
                                                <span className="transcript-item-avatar">👤</span>
                                                <div className="transcript-item-meta">
                                                    <h4>{interview.persona.name}</h4>
                                                    <span>{interview.persona.role}</span>
                                                </div>
                                            </div>
                                            <div className="transcript-item-scores">
                                                <span>🔥 Pain: {interview.pain_level}/10</span>
                                                <span>💰 WTP: {interview.willingness_to_pay}/10</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default IterationCard;
