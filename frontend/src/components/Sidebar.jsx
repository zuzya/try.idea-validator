import useValidationStore from '../store/useValidationStore';

function Sidebar() {
    const { status, config, setConfig } = useValidationStore();
    const isRunning = status === 'running';

    return (
        <aside className="sidebar" style={{ backgroundColor: 'var(--c-paper-2)' }}>
            <div className="sidebar-header" style={{ marginBottom: '2rem' }}>
                <h1 style={{ letterSpacing: '-1px', margin: 0, lineHeight: 1 }}>
                    <span style={{ color: 'var(--c-ink)', fontSize: '2.5rem', display: 'block' }}>UNI</span>
                    <span style={{ color: 'var(--c-primary)', fontSize: '2.5rem', display: 'block' }}>CORN</span>
                    <span style={{ fontSize: '1rem', color: 'var(--c-ink)', fontFamily: 'var(--font-body)', fontWeight: 'bold' }}>VOL. 1</span>
                </h1>
            </div>

            <div style={{ padding: '0 1rem' }}>
                {/* Status Indicator */}
                <div className="status-indicator" style={{
                    border: 'var(--border-width) solid var(--c-ink)',
                    padding: '0.8rem',
                    background: 'var(--c-panel)',
                    marginBottom: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    boxShadow: '4px 4px 0 var(--c-ink)'
                }}>
                    <div className={`status-dot ${status === 'running' ? 'processing' : status === 'complete' ? 'active' : 'idle'}`}
                        style={{
                            width: '20px',
                            height: '20px',
                            background: status === 'running' ? 'var(--c-highlight)' : status === 'complete' ? 'var(--c-success)' : '#ccc',
                            border: '2px solid var(--c-ink)',
                            borderRadius: '0'
                        }}>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 'bold', textTransform: 'uppercase', fontSize: '1.1rem', color: 'var(--c-ink)' }}>
                        {status === 'idle' && 'READY'}
                        {status === 'running' && 'PRINTING...'}
                        {status === 'complete' && 'PUBLISHED'}
                        {status === 'error' && 'JAMMED'}
                    </span>
                </div>

                <div className="divider" style={{ borderTop: '2px dashed var(--c-ink)', margin: '1rem 0', opacity: 0.3 }}></div>

                {/* Modes (Moved to Top) */}
                <div className="sidebar-section">
                    <span className="sidebar-section-title">Modes</span>

                    {/* Enable Critic First */}
                    <label className="checkbox-label" style={{ background: 'var(--c-panel)', padding: '0.5rem', border: '1px solid var(--c-ink)', display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '0.5rem' }}>
                        <input
                            type="checkbox"
                            checked={config.enableCritic}
                            onChange={(e) => setConfig('enableCritic', e.target.checked)}
                            disabled={isRunning}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem' }}>Enable Critic</span>
                    </label>

                    <label className="checkbox-label" style={{ background: 'var(--c-panel)', padding: '0.5rem', border: '1px solid var(--c-ink)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={config.enableSimulation}
                            onChange={(e) => setConfig('enableSimulation', e.target.checked)}
                            disabled={isRunning}
                            style={{ marginRight: '0.5rem' }}
                        />
                        <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem' }}>Run Simulation</span>
                    </label>
                </div>

                <div className="divider" style={{ borderTop: '2px dashed var(--c-ink)', margin: '1rem 0', opacity: 0.3 }}></div>

                {/* Configuration */}
                <div className="sidebar-section">
                    <span className="sidebar-section-title">Configuration</span>

                    {/* Conditional Max Iterations Slider */}
                    {config.enableCritic && (
                        <div className="slider-container" style={{ background: 'var(--c-panel)', padding: '0.5rem', border: '1px solid var(--c-ink)', marginBottom: '1rem' }}>
                            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span className="slider-label" style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem' }}>Max Iterations</span>
                                <span className="slider-value" style={{ fontWeight: 'bold' }}>{config.maxIterations}</span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="5"
                                value={config.maxIterations}
                                onChange={(e) => setConfig('maxIterations', parseInt(e.target.value))}
                                disabled={isRunning}
                                style={{ width: '100%', accentColor: 'var(--c-primary)' }}
                            />
                        </div>
                    )}

                    {/* Conditional Respondents Slider */}
                    {config.enableSimulation && (
                        <div className="slider-container" style={{ background: 'var(--c-panel)', padding: '0.5rem', border: '1px solid var(--c-ink)', marginBottom: '1rem' }}>
                            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span className="slider-label" style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem' }}>Respondents</span>
                                <span className="slider-value" style={{ fontWeight: 'bold' }}>{config.numPersonas}</span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="5"
                                value={config.numPersonas}
                                onChange={(e) => setConfig('numPersonas', parseInt(e.target.value))}
                                disabled={isRunning}
                                style={{ width: '100%', accentColor: 'var(--c-primary)' }}
                            />
                        </div>
                    )}

                    {/* Heavy Thinking (Inverted Fast Model) */}
                    <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '0.9rem', marginTop: '1rem' }}>
                        <input
                            type="checkbox"
                            checked={!config.useFastModel}
                            onChange={(e) => setConfig('useFastModel', !e.target.checked)}
                            disabled={isRunning}
                            style={{ marginRight: '0.5rem' }}
                        />
                        Heavy Thinking
                    </label>
                </div>
            </div>

            <div style={{ padding: '1.5rem', marginTop: 'auto' }}>
                <div className="badge" style={{ background: 'var(--c-ink)', border: '2px solid var(--c-panel)', color: 'var(--c-panel)', width: '100%', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
                    Google Gemini / OpenAi ChatGpt inside
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
