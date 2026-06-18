import React, { useState } from 'react';
import axios from 'axios';
import SuggestionDisplay from './SuggestionDisplay';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

function FeedbackForm({ onFeedbackSubmitted }) {
    const [text, setText] = useState('');
    const [domain, setDomain] = useState('engineering');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [suggestionData, setSuggestionData] = useState(null);

    const domains = [
        { value: 'engineering', label: '👨‍💻 Engineering & Technology', icon: '👨‍💻' },
        { value: 'commerce', label: '💼 Commerce & Business', icon: '💼' },
        { value: 'science', label: '🔬 Science & Research', icon: '🔬' },
        { value: 'arts', label: '🎨 Arts & Design', icon: '🎨' },
        { value: 'medical', label: '⚕️ Medical & Healthcare', icon: '⚕️' },
        { value: 'law', label: '⚖️ Law & Legal Studies', icon: '⚖️' },
        { value: 'management', label: '📊 Management & MBA', icon: '📊' },
        { value: 'other', label: '📚 Other', icon: '📚' }
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setSuggestionData(null);
        if (!text.trim()) {
            setError('Please enter feedback.');
            return;
        }
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/api/feedback`, {
                feedback_text: text,
                domain: domain
            });
            setSuccess('Submitted! Sentiment: ' + res.data.sentiment_label);
            // Pass entire response so the download component has feedback + sentiment + suggestion
            setSuggestionData(res.data);
            setText('');

            // Notify parent component that feedback was submitted
            if (onFeedbackSubmitted) {
                onFeedbackSubmitted(res.data);
            }
        } catch (err) {
            setError(err?.response?.data?.error || 'Submission failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Domain Selector */}
                <div className="bg-neutral/30 rounded-2xl p-6 border border-neutral-light/30">
                    <label className="block text-sm font-medium text-text-primary mb-3">
                        Select Your Domain / Field of Study
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {domains.map((d) => (
                            <button
                                key={d.value}
                                type="button"
                                onClick={() => setDomain(d.value)}
                                className={`p-3 rounded-xl border-2 transition-all duration-200 text-left ${domain === d.value
                                    ? 'border-primary bg-primary/10 shadow-lg shadow-primary/20'
                                    : 'border-neutral-light/30 bg-neutral/50 hover:border-primary/50'
                                    }`}
                            >
                                <div className="text-2xl mb-1">{d.icon}</div>
                                <div className="text-xs text-text-primary font-medium">
                                    {d.label.replace(/[^\w\s&]/g, '').trim()}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Feedback Text Area */}
                <div className="relative">
                    <textarea
                        className="w-full rounded-2xl border border-neutral-light/50 bg-neutral/50 p-4 md:p-6 text-text-primary placeholder:text-text-secondary/70 focus:border-primary focus:ring-2 focus:ring-primary/40 focus:outline-none transition-all duration-300 resize-none"
                        rows={6}
                        placeholder={`Share detailed employer feedback here... (Selected domain: ${domains.find(d => d.value === domain)?.label || 'Engineering'})`}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                    />
                    <div className="absolute bottom-4 right-4 text-xs text-text-secondary">
                        {text.length} characters
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <button
                        type="submit"
                        className="btn-primary w-full sm:w-auto"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <span className="mr-2">🚀</span>
                                Analyze & Submit
                            </>
                        )}
                    </button>

                    <div className="flex items-center space-x-4">
                        {error && (
                            <div className="flex items-center text-red-400">
                                <span className="mr-2">⚠️</span>
                                <span className="text-sm">{error}</span>
                            </div>
                        )}
                        {success && (
                            <div className="flex items-center text-green-400">
                                <span className="mr-2">✅</span>
                                <div className="text-sm">
                                    <div>{success}</div>
                                    <div className="text-text-secondary mt-1">
                                        Check "Feedback History" tab to see all your submissions.
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <SuggestionDisplay suggestionData={suggestionData} />
            </form>
        </div>
    );
}

export default FeedbackForm;
