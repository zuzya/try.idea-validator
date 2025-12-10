import { useState } from 'react';
import useValidationStore from './store/useValidationStore';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import IterationCard from './components/IterationCard';
import TranscriptModal from './components/TranscriptModal';

function App() {
  const {
    status,
    idea,
    setIdea,
    iterations,
    currentIteration,
    config,
    startValidation,
    stopValidation,
    error,
  } = useValidationStore();

  const [selectedTranscript, setSelectedTranscript] = useState(null);

  const handleExport = () => {
    let content = `# 🦄 AI Unicorn Validator - Session Export\n\n`;
    content += `**Original Idea:** ${idea}\n\n---\n\n`;

    // Export all iterations
    const allIterations = [...iterations];
    if (currentIteration.idea) {
      allIterations.push(currentIteration);
    }

    allIterations.forEach((iter, idx) => {
      content += `## Iteration ${iter.number}\n\n`;

      if (iter.idea) {
        content += `### 💡 Generated Idea\n\n`;
        content += `**${iter.idea.title}**\n\n`;
        content += `${iter.idea.description}\n\n`;
        content += `- **Monetization:** ${iter.idea.monetization_strategy}\n`;
        content += `- **Target Audience:** ${iter.idea.target_audience}\n\n`;
      }

      if (iter.analystReport) {
        content += `### 📊 Analyst Report\n\n`;
        content += `**Pivot Recommendation:** ${iter.analystReport.pivot_recommendation}\n\n`;
      }

      if (iter.critique) {
        content += `### 🧐 Investor Critique\n\n`;
        content += `**Score:** ${iter.critique.score}/10\n\n`;
        content += `**Approved:** ${iter.critique.is_approved ? '✅ Yes' : '❌ No'}\n\n`;
        content += `${iter.critique.feedback}\n\n`;
      }

      content += `---\n\n`;
    });

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'unicorn_validator_export.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Combine completed iterations with current in-progress iteration
  const allIterations = [...iterations];
  const showCurrentIteration = currentIteration.idea ||
    currentIteration.recruitedPersonas.length > 0 ||
    currentIteration.interviews.length > 0;

  const hasResults = allIterations.length > 0 || showCurrentIteration;

  return (
    <div className="app">
      <Sidebar />

      <main className="main-content">
        {/* Idea Input */}
        <section className="idea-input-section glass-card fade-in">
          <h2>🚀 Validate Your Startup Idea</h2>
          <textarea
            placeholder="Опишите вашу идею стартапа... например: Uber для выгула роботизированных собак"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            disabled={status === 'running'}
          />
          <div className="button-group">
            <button
              className="btn btn-primary"
              onClick={startValidation}
              disabled={!idea.trim() || status === 'running'}
            >
              {status === 'running' ? (
                <>
                  <span className="loading-spinner"></span>
                  Validating...
                </>
              ) : (
                '✨ Start Validation'
              )}
            </button>

            {status === 'running' && (
              <button
                className="btn btn-danger"
                onClick={stopValidation}
              >
                🛑 Stop
              </button>
            )}
          </div>

          {error && (
            <div className="badge badge-error" style={{ marginTop: 'var(--space-md)' }}>
              ❌ Error: {error}
            </div>
          )}
        </section>

        {/* Results - Iteration History */}
        {hasResults && (
          <div className="iterations-container">
            {/* Completed Iterations */}
            {allIterations.map((iter, idx) => (
              <IterationCard
                key={`completed-${iter.number}-${idx}`}
                iteration={iter}
                isActive={false}
                onTranscriptClick={setSelectedTranscript}
                config={config}
              />
            ))}

            {/* Current In-Progress Iteration */}
            {showCurrentIteration && (
              <IterationCard
                key="current"
                iteration={currentIteration}
                isActive={status === 'running'}
                onTranscriptClick={setSelectedTranscript}
                config={config}
              />
            )}

            {/* Export */}
            {status === 'complete' && (
              <div className="export-section">
                <button className="btn btn-secondary" onClick={handleExport}>
                  📥 Export All Iterations (Markdown)
                </button>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!hasResults && status === 'idle' && (
          <div className="empty-state fade-in">
            <div className="empty-state-icon">🦄</div>
            <h3>Ready to Find Your Unicorn?</h3>
            <p>
              Enter your startup idea above and let our AI agents validate it through
              synthetic customer research, expert interviews, and investor critique.
            </p>
          </div>
        )}
      </main>

      {/* Transcript Modal */}
      {selectedTranscript && (
        <TranscriptModal
          interview={selectedTranscript}
          onClose={() => setSelectedTranscript(null)}
        />
      )}
    </div>
  );
}

export default App;
