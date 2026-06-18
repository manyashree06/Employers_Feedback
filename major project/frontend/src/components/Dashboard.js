import React from 'react';
import { useData } from '../context/DataContext';
import { LoadingSpinner, ErrorDisplay } from './common/LoadingComponents';

function Dashboard() {
    const { stats, loading, error, refreshData } = useData();

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <LoadingSpinner text="Processing sentiment analysis from dataset..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center py-12">
                <ErrorDisplay error={error} onRetry={refreshData} />
            </div>
        );
    }

    if (!stats || stats.total === 0) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center text-text-secondary">
                    <div className="text-4xl mb-2">📊</div>
                    <div>No feedback data available</div>
                </div>
            </div>
        );
    }

    const getSentimentColor = (score) => {
        if (typeof score !== 'number' || isNaN(score)) return 'text-gray-400';
        if (score > 0.1) return 'text-green-400';
        if (score < -0.1) return 'text-red-400';
        return 'text-yellow-400';
    };

    const getSentimentEmoji = (score) => {
        if (typeof score !== 'number' || isNaN(score)) return '😐';
        if (score > 0.1) return '😊';
        if (score < -0.1) return '😞';
        return '😐';
    };

    const formatScore = (score) => {
        return typeof score === 'number' && !isNaN(score) ? score.toFixed(3) : '0.000';
    };

    const formatPercentage = (numerator, total) => {
        if (!total || total === 0) return '0.0';
        return ((numerator / total) * 100).toFixed(1);
    };

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            <div className="card p-4 md:p-6 text-center group hover:scale-105 transition-transform duration-300">
                <div className="text-4xl mb-2">📊</div>
                <div className="text-sm text-text-secondary mb-1">Total Feedback</div>
                <div className="text-3xl font-bold text-primary">{stats.total || 0}</div>
            </div>

            <div className="card p-4 md:p-6 text-center group hover:scale-105 transition-transform duration-300">
                <div className="text-4xl mb-2">{getSentimentEmoji(stats.avg_sentiment_score)}</div>
                <div className="text-sm text-text-secondary mb-1">Average Sentiment</div>
                <div className={`text-3xl font-bold ${getSentimentColor(stats.avg_sentiment_score)}`}>
                    {formatScore(stats.avg_sentiment_score)}
                </div>
            </div>

            <div className="card p-4 md:p-6 text-center group hover:scale-105 transition-transform duration-300 border border-green-500/30">
                <div className="text-4xl mb-2">✅</div>
                <div className="text-sm text-text-secondary mb-1">Positive</div>
                <div className="text-3xl font-bold text-green-400">{stats.count_positive || 0}</div>
                <div className="text-xs text-text-secondary/80 mt-1">
                    {formatPercentage(stats.count_positive, stats.total)}%
                </div>
            </div>

            <div className="card p-4 md:p-6 text-center group hover:scale-105 transition-transform duration-300 border border-red-500/30">
                <div className="text-4xl mb-2">❌</div>
                <div className="text-sm text-text-secondary mb-1">Negative</div>
                <div className="text-3xl font-bold text-red-400">{stats.count_negative || 0}</div>
                <div className="text-xs text-text-secondary/80 mt-1">
                    {formatPercentage(stats.count_negative, stats.total)}%
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
