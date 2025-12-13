import { useState } from 'react';
import IdeaCard from './IdeaCard';
import PersonaCard from './PersonaCard';
import InterviewProgress from './InterviewProgress';
import AnalystReport from './AnalystReport';
import CritiqueCard from './CritiqueCard';
import ResearchGuide from './ResearchGuide';

function IterationCard({ iteration, isActive, onTranscriptClick, config }) {
    const [isExpanded, setIsExpanded] = useState(isActive);

    const {
        number,
        idea,
        recruitedPersonas,
        interviews,
        analystReport,
        critique,
        researchGuide,
    } = iteration;

    return (
        <div className={`iteration-card ${isActive ? 'active' : ''}`} style={{ marginBottom: '2rem' }}>
            {/* Header / Spine */}
            <div
                className="iteration-header"
                onClick={() => setIsExpanded(!isExpanded)}
                style={{
                    background: isActive ? 'var(--c-primary)' : 'var(--c-ink-soft)',
                    color: isActive ? 'var(--c-panel)' : 'var(--c-panel)', /* White text on both */
                    padding: '1rem',
                    cursor: 'pointer',
                    border: '3px solid var(--c-ink)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: isActive ? 'none' : '4px 4px 0 rgba(0,0,0,0.3)',
                    transform: isActive ? 'translate(2px, 2px)' : 'none',
                    transition: 'all 0.2s'
                }}
            >
                <div className="iteration-header-left" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '1.5rem' }}>{isExpanded ? '👐' : '📕'}</span>
                    <h3 className="iteration-title" style={{ margin: 0, fontFamily: 'var(--font-headline)', fontSize: '1.8rem', color: 'inherit' }}>
                        ISSUE #{number}
                        {idea && <span style={{ fontFamily: 'var(--font-body)', fontSize: '1rem', marginLeft: '1rem', opacity: 0.8 }}>: {idea.title}</span>}
                    </h3>
                </div>

                {isActive && <span className="badge pulse" style={{ background: 'var(--c-highlight)', color: 'var(--c-ink)', border: '2px solid var(--c-ink)' }}>IN PRODUCTION</span>}
            </div>

            {/* Content (The Pages) */}
            {isExpanded && (
                <div className="iteration-content" style={{
                    border: '3px solid var(--c-ink)',
                    borderTop: 'none',
                    padding: '2rem',
                    background: 'var(--c-paper)',
                    backgroundImage: 'radial-gradient(var(--c-muted) 1px, transparent 1px)',
                    backgroundSize: '20px 20px'
                }}>

                    {/* 1. The Idea Panel */}
                    {idea && (
                        <div className="iteration-section">
                            <IdeaCard idea={idea} iteration={number} />
                        </div>
                    )}

                    {/* 1.5 The Research Guide */}
                    {researchGuide && (
                        <div className="iteration-section" style={{ marginTop: '2rem' }}>
                            <ResearchGuide guide={researchGuide} />
                        </div>
                    )}

                    {/* 2. The Lineup (Personas) */}
                    {recruitedPersonas && recruitedPersonas.length > 0 && (
                        <div className="iteration-section" style={{ marginTop: '2rem' }}>
                            <h3 style={{ background: 'var(--c-ink)', color: 'var(--c-panel)', display: 'inline-block', padding: '0.2rem 1rem', transform: 'rotate(-2deg)' }}>THE LINEUP</h3>
                            <div className="persona-grid" style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                                gap: '1.5rem',
                                marginTop: '1rem'
                            }}>
                                {recruitedPersonas.map((persona, idx) => (
                                    <PersonaCard key={idx} persona={persona} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 3. The Interview Log */}
                    {((interviews && interviews.length > 0) || (isActive && recruitedPersonas?.length > 0)) && (
                        <div className="iteration-section" style={{ marginTop: '2rem' }}>
                            <InterviewProgress
                                interviews={interviews || []}
                                totalPersonas={config?.numPersonas || recruitedPersonas?.length || 3}
                                isRunning={isActive && (!interviews || interviews.length < (config?.numPersonas || 3))}
                            />
                        </div>
                    )}

                    {/* 4. Analyst Dossier */}
                    {analystReport && (
                        <div className="iteration-section" style={{ marginTop: '3rem' }}>
                            <AnalystReport report={analystReport} />
                        </div>
                    )}

                    {/* 5. The Verdict */}
                    {critique && (
                        <div className="iteration-section" style={{ marginTop: '3rem' }}>
                            <CritiqueCard critique={critique} />
                        </div>
                    )}

                    {/* 6. Transcripts (Nav) */}
                    {interviews && interviews.length > 0 && (
                        <div className="iteration-section" style={{ marginTop: '2rem', textAlign: 'center' }}>
                            <h4 style={{ fontFamily: 'var(--font-headline)', marginBottom: '1rem' }}>READ FULL TRANSCRIPTS</h4>
                            <div className="transcript-list" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'center' }}>
                                {interviews.map((interview, idx) => (
                                    <button
                                        key={idx}
                                        className="btn btn-secondary"
                                        style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onTranscriptClick(interview);
                                        }}
                                    >
                                        📄 {interview.persona.name}'s TAPE
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default IterationCard;
