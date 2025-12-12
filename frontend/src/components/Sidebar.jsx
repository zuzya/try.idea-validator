import useValidationStore from '../store/useValidationStore';

function Sidebar() {
    const { status, config, setConfig } = useValidationStore();
    const isRunning = status === 'running';

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <h1>🦄 VALIDATOR<br /><span style={{ fontSize: '1.2rem', color: 'var(--c-magenta)' }}>Issue #1</span></h1>
            </div>

            <div className="status-indicator" style={{ border: '2px solid black', padding: '0.5rem', background: '#fff' }}>
                <div className={`status-dot ${status === 'running' ? 'processing' : status === 'complete' ? 'active' : 'idle'}`}
                    style={{ width: '12px', height: '12px', background: status === 'running' ? 'var(--c-yellow)' : status === 'complete' ? 'var(--c-cyan)' : '#ccc', border: '2px solid black' }}>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 'bold', textTransform: 'uppercase' }}>
                    {status === 'idle' && 'READY'}
                    {status === 'running' && 'PRINTING...'}
                    {status === 'complete' && 'PUBLISHED'}
                    {status === 'error' && 'JAMMED'}
                </span>
            </div>

            <div className="divider"></div>

            <div className="sidebar-section">
                <span className="sidebar-section-title">Configuration</span>

                <div className="slider-container">
                    <div className="slider-header">
                        <span className="slider-label">Max Iterations</span>
                        <span className="slider-value">{config.maxIterations}</span>
                    </div>
                    <input
                        type="range"
                        min="1"
                        max="10"
                        value={config.maxIterations}
                        onChange={(e) => setConfig('maxIterations', parseInt(e.target.value))}
                        disabled={isRunning}
                    />
                </div>

                <div className="slider-container">
                    <div className="slider-header">
                        <span className="slider-label">Number of Respondents</span>
                        <span className="slider-value">{config.numPersonas}</span>
                    </div>
                    <input
                        type="range"
                        min="1"
                        max="3"
                        value={config.numPersonas}
                        onChange={(e) => setConfig('numPersonas', parseInt(e.target.value))}
                        disabled={isRunning}
                    />
                </div>

                <div className="slider-container">
                    <div className="slider-header">
                        <span className="slider-label">Interview Cycles</span>
                        <span className="slider-value">{config.interviewIterations}</span>
                    </div>
                    <input
                        type="range"
                        min="1"
                        max="3"
                        value={config.interviewIterations}
                        onChange={(e) => setConfig('interviewIterations', parseInt(e.target.value))}
                        disabled={isRunning}
                    />
                </div>
            </div>

            <div className="divider"></div>

            <div className="sidebar-section">
                <span className="sidebar-section-title">Validation Modes</span>

                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={config.enableSimulation}
                        onChange={(e) => setConfig('enableSimulation', e.target.checked)}
                        disabled={isRunning}
                    />
                    Run Simulation (Research & Interviews)
                </label>

                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={config.enableCritic}
                        onChange={(e) => setConfig('enableCritic', e.target.checked)}
                        disabled={isRunning}
                    />
                    Enable Investor Critic
                </label>
            </div>

            <div className="divider"></div>

            <div className="sidebar-section">
                <span className="sidebar-section-title">Debug Options</span>

                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={config.mockSimulation}
                        onChange={(e) => setConfig('mockSimulation', e.target.checked)}
                        disabled={isRunning}
                    />
                    ⚡ Mock Interviews (faster)
                </label>

                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={config.useFastModel}
                        onChange={(e) => setConfig('useFastModel', e.target.checked)}
                        disabled={isRunning}
                    />
                    ⚡ Debug Mode (Fast Models)
                </label>
            </div>

            <div style={{ marginTop: 'auto', paddingTop: 'var(--space-lg)' }}>
                <div className="badge badge-info">
                    Powered by Gemini 3.0 Pro & GPT-5.1
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
