import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LoadingSpinner, ErrorDisplay } from './common/LoadingComponents';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

function FeedbackList({ refreshTrigger }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const load = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await axios.get(`${API_BASE}/api/feedback`);
            setItems(res.data);
        } catch (err) {
            const errorMessage = err.response?.data?.error ||
                err.code === 'ECONNABORTED' ? 'Request timeout' :
                err.code === 'ECONNREFUSED' ? 'Cannot connect to server' :
                    'Failed to load feedback history';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [refreshTrigger]); // Refresh when trigger changes

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <LoadingSpinner text="Loading feedback history..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center py-12">
                <ErrorDisplay error={error} onRetry={load} />
            </div>
        );
    }

    const getSentimentColor = (label) => {
        switch (label) {
            case 'Positive': return 'text-green-400 bg-green-500/10 border-green-500/20';
            case 'Negative': return 'text-red-400 bg-red-500/10 border-red-500/20';
            default: return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
        }
    };

    const getSentimentEmoji = (label) => {
        switch (label) {
            case 'Positive': return '😊';
            case 'Negative': return '😞';
            default: return '😐';
        }
    };

    const getDomainInfo = (domain) => {
        const domains = {
            'engineering': { icon: '👨‍💻', label: 'Engineering' },
            'commerce': { icon: '💼', label: 'Commerce' },
            'science': { icon: '🔬', label: 'Science' },
            'arts': { icon: '🎨', label: 'Arts' },
            'medical': { icon: '⚕️', label: 'Medical' },
            'law': { icon: '⚖️', label: 'Law' },
            'management': { icon: '📊', label: 'Management' },
            'other': { icon: '📚', label: 'Other' }
        };
        return domains[domain] || { icon: '👨‍💻', label: 'Engineering' };
    };

    return (
        <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between mb-6 gap-4">
                <h3 className="text-lg font-semibold text-text-primary">Recent Feedback Entries</h3>
                <div className="flex items-center space-x-4">
                    <div className="text-sm text-text-secondary">{items.length} total entries</div>
                    <button
                        onClick={load}
                        className="px-3 py-1 bg-primary/20 text-primary rounded text-sm hover:bg-primary/30 transition-colors"
                        title="Refresh feedback list"
                    >
                        🔄 Refresh
                    </button>
                </div>
            </div>

            <div className="space-y-4 max-h-[40rem] overflow-y-auto pr-2">
                {items.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-6xl mb-4">📝</div>
                        <h3 className="text-xl font-semibold text-text-primary mb-2">No feedback yet</h3>
                        <p className="text-text-secondary">Submit your first feedback to see it here!</p>
                    </div>
                ) : (
                    items.map((item) => {
                        const domainInfo = getDomainInfo(item.domain);
                        return (
                            <div key={item.id} className="card p-4 md:p-6 hover:scale-[1.02] transition-transform duration-300">
                                <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                                    <div className="flex items-center space-x-3">
                                        <div className="text-2xl">{getSentimentEmoji(item.sentiment_label)}</div>
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getSentimentColor(item.sentiment_label)}`}>
                                                    {item.sentiment_label}
                                                </div>
                                                {item.domain && (
                                                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                                                        <span className="mr-1">{domainInfo.icon}</span>
                                                        {domainInfo.label}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="text-xs text-text-secondary mt-1">
                                                {new Date(item.timestamp).toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                    {/* Sentiment score hidden as per requirements */}
                                    {/* <div className="text-right">
                                        <div className="text-lg font-bold text-primary">
                                            {item.sentiment_score.toFixed(3)}
                                        </div>
                                        <div className="text-xs text-text-secondary">Sentiment Score</div>
                                    </div> */}
                                </div>
                                <p className="text-text-primary mt-4">{item.feedback_text}</p>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default FeedbackList;
