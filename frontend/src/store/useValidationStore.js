import { create } from 'zustand';

// AbortController for cancelling requests
let abortController = null;

const useValidationStore = create((set, get) => ({
    // State
    status: 'idle', // idle | running | complete | error | stopped
    idea: '',

    // Config
    config: {
        maxIterations: 5,
        numPersonas: 3,
        interviewIterations: 1,
        mockSimulation: false,
        enableSimulation: true,
        enableCritic: true,
        useFastModel: false,
    },

    // Iteration History - array of complete iteration snapshots
    iterations: [],

    // Current iteration data (work in progress)
    currentIteration: {
        number: 0,
        idea: null,
        researchGuide: null,
        recruitedPersonas: [],
        interviews: [],
        analystReport: null,
        critique: null,
    },

    // Error
    error: null,

    // Actions
    setIdea: (idea) => set({ idea }),

    setConfig: (key, value) => set((state) => ({
        config: { ...state.config, [key]: value }
    })),

    reset: () => set({
        status: 'idle',
        iterations: [],
        currentIteration: {
            number: 0,
            idea: null,
            researchGuide: null,
            recruitedPersonas: [],
            interviews: [],
            analystReport: null,
            critique: null,
        },
        error: null,
    }),

    // STOP - Emergency stop button
    stopValidation: () => {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
        set({
            status: 'stopped',
            error: 'Validation stopped by user'
        });
    },

    // Helper: save current iteration to history and start new one
    saveCurrentIteration: () => {
        const { currentIteration, iterations } = get();

        // Only save if there's actual data
        if (currentIteration.idea) {
            set({
                iterations: [...iterations, { ...currentIteration }],
                currentIteration: {
                    number: currentIteration.number + 1,
                    idea: null,
                    researchGuide: null,
                    recruitedPersonas: [],
                    interviews: [],
                    analystReport: null,
                    critique: null,
                }
            });
        }
    },

    // SSE Event Handlers
    handleEvent: (eventType, data) => {
        // Check if aborted
        if (get().status === 'stopped') return;

        const handlers = {
            start: () => set({ status: 'running', error: null }),

            generator: (data) => {
                const { iterations, currentIteration } = get();

                // If we already have an idea in current iteration, this is a NEW iteration
                // Save the old one first
                if (currentIteration.idea && currentIteration.critique) {
                    get().saveCurrentIteration();
                }

                set((state) => ({
                    currentIteration: {
                        ...state.currentIteration,
                        number: data.iteration,
                        idea: data.idea,
                        // Reset other fields for new iteration
                        researchGuide: null,
                        recruitedPersonas: [],
                        interviews: [],
                        analystReport: null,
                        critique: null,
                    }
                }));
            },

            researcher: (data) => set((state) => ({
                currentIteration: {
                    ...state.currentIteration,
                    researchGuide: data,
                }
            })),

            recruiter: (data) => set((state) => ({
                currentIteration: {
                    ...state.currentIteration,
                    recruitedPersonas: data.personas,
                }
            })),

            simulation: (data) => set((state) => ({
                currentIteration: {
                    ...state.currentIteration,
                    interviews: [...state.currentIteration.interviews, ...data.interviews],
                }
            })),

            analyst: (data) => set((state) => ({
                currentIteration: {
                    ...state.currentIteration,
                    analystReport: data,
                }
            })),

            critic: (data) => set((state) => ({
                currentIteration: {
                    ...state.currentIteration,
                    critique: data,
                }
            })),

            complete: () => {
                // Save the final iteration when complete
                const { currentIteration, iterations } = get();
                if (currentIteration.idea) {
                    set({
                        status: 'complete',
                        iterations: [...iterations, { ...currentIteration }],
                    });
                } else {
                    set({ status: 'complete' });
                }
            },

            error: (data) => set({
                status: 'error',
                error: data.message
            }),
        };

        const handler = handlers[eventType];
        if (handler) {
            handler(data);
        }
    },

    // Start validation
    startValidation: async () => {
        const { idea, config } = get();
        if (!idea.trim()) return;

        // Create new AbortController
        abortController = new AbortController();

        // Reset previous results
        get().reset();
        set({ status: 'running', idea });

        try {
            const response = await fetch('http://localhost:8000/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    idea: idea,
                    max_iterations: config.maxIterations,
                    num_personas: config.numPersonas,
                    interview_iterations: config.interviewIterations,
                    mock_simulation: config.mockSimulation,
                    enable_simulation: config.enableSimulation,
                    enable_critic: config.enableCritic,
                    use_fast_model: config.useFastModel,
                }),
                signal: abortController.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                if (get().status === 'stopped') {
                    reader.cancel();
                    break;
                }

                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                let eventType = null;
                let eventData = null;

                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        eventType = line.slice(7);
                    } else if (line.startsWith('data: ')) {
                        try {
                            eventData = JSON.parse(line.slice(6));
                        } catch (e) {
                            console.error('Failed to parse event data:', e);
                        }
                    } else if (line === '' && eventType && eventData) {
                        get().handleEvent(eventType, eventData);
                        eventType = null;
                        eventData = null;
                    }
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Validation aborted by user');
                return;
            }

            console.error('Validation error:', error);
            set({
                status: 'error',
                error: error.message
            });
        } finally {
            abortController = null;
        }
    },
}));

export default useValidationStore;
