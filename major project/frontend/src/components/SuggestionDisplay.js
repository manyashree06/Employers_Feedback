import React, { useState } from 'react';

const SuggestionDisplay = ({ suggestionData }) => {
    const [expandedSection, setExpandedSection] = useState(null);

    if (!suggestionData) return (
        <div className="flex items-center justify-center p-8 bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-xl mt-4 border border-gray-700/50 shadow-lg backdrop-blur-sm">
            <p className="text-gray-300 text-center text-lg font-medium bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Submit your feedback to get personalized suggestions
            </p>
        </div>
    );

    // Debug logging to track data flow
    console.log('Raw suggestion data:', suggestionData);

    // Helper function to ensure arrays are actually arrays
    const ensureArray = (data) => {
        if (!data) return [];
        if (Array.isArray(data)) return data;
        if (typeof data === 'object') return Object.values(data);
        if (typeof data === 'string') return [data];
        return [];
    };

    // Enhanced data normalization with improved validation
    const normalizeData = (data) => {
        try {
            // Handle string data
            if (typeof data === 'string') {
                try {
                    const parsed = JSON.parse(data);
                    console.log('Parsed string data:', parsed);
                    return normalizeData(parsed); // Recursively process parsed data
                } catch (e) {
                    console.log('Basic string suggestion:', data);
                    return { type: 'basic', suggestion: data };
                }
            }

            // Handle object data with validation
            if (typeof data === 'object' && data !== null) {
                // Case 1: Response object with nested suggestion object
                if (data.suggestion && typeof data.suggestion === 'object') {
                    console.log('Found nested suggestion object');
                    return normalizeData(data.suggestion); // Extract and process the suggestion
                }

                // Case 2: Response object with string suggestion
                if (data.suggestion && typeof data.suggestion === 'string') {
                    console.log('Basic string suggestion in response');
                    return {
                        type: 'basic',
                        feedback_text: data.feedback_text || '',
                        sentiment_label: data.sentiment_label || '',
                        suggestion: data.suggestion
                    };
                }

                // Case 3: Advanced format with full structure (direct suggestion object)
                if (data.title && data.immediate_actions) {
                    console.log('Advanced suggestion format detected');
                    return {
                        type: 'advanced',
                        ...data,
                        // Ensure all arrays are actually arrays
                        immediate_actions: ensureArray(data.immediate_actions),
                        weekly_goals: ensureArray(data.weekly_goals),
                        resources: ensureArray(data.resources),
                        success_metrics: ensureArray(data.success_metrics || data.key_metrics),
                        recurring_themes: data.pattern_insights?.recurring_themes
                            ? ensureArray(data.pattern_insights.recurring_themes)
                            : []
                    };
                }

                // Case 4: Check for any other object that might have feedback data
                if (data.feedback_text) {
                    console.log('Object with feedback_text but no clear suggestion');
                    return null; // Return null to show "no suggestions" message
                }
            }

            console.warn('Unhandled data format:', data);
            return null;
        } catch (error) {
            console.error('Error normalizing suggestion data:', error);
            return { type: 'basic', suggestion: 'Error processing suggestion data' };
        }
    };

    const normalized = normalizeData(suggestionData);

    console.log('Normalized data:', normalized);

    // If normalization failed or returned null, show message
    if (!normalized) {
        return (
            <div className="flex items-center justify-center p-6 bg-gray-50 rounded-lg mt-4">
                <p className="text-gray-600 text-center">Processing suggestions...</p>
            </div>
        );
    }

    // Enhanced display logic with better error handling
    if (typeof normalized === 'string' || normalized?.type === 'basic') {
        const suggestionText = typeof normalized === 'string' ? normalized : (normalized?.suggestion || '');
        if (!suggestionText) {
            return (
                <div className="flex items-center justify-center p-6 bg-gray-50 rounded-lg mt-4">
                    <p className="text-gray-600 text-center">No suggestions available</p>
                </div>
            );
        }
        return (
            <div style={{
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '24px',
                marginTop: '24px',
                backgroundColor: '#f8fafc'
            }}>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                    <button
                        type="button"
                        onClick={async () => {
                            try {
                                const payload = {
                                    feedback: suggestionData.feedback_text || '',
                                    sentiment: suggestionData.sentiment_label || '',
                                    suggestion: suggestionText
                                };
                                const res = await fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:5000'}/generate-report`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(payload),
                                });
                                if (!res.ok) throw new Error('Failed to generate report');
                                const blob = await res.blob();
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'Feedback_Report.pdf';
                                document.body.appendChild(a);
                                a.click();
                                a.remove();
                                window.URL.revokeObjectURL(url);
                            } catch (err) {
                                console.error('Error downloading report', err);
                                alert('Could not download report. Please try again.');
                            }
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                        Download Personalized Report
                    </button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '24px', marginRight: '12px' }}>💡</span>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#1e40af' }}>AI Suggestion</h3>
                </div>
                <p style={{ color: '#64748b', lineHeight: '1.6' }}>{suggestionText}</p>
            </div>
        );
    }

    const toggleSection = (section) => {
        console.log('Toggling section:', section, 'Current expanded:', expandedSection);
        setExpandedSection(prev => {
            const newSection = prev === section ? null : section;
            console.log('New expanded section:', newSection);
            return newSection;
        });
    };

    const getUrgencyColor = (urgency) => {
        switch (urgency?.toLowerCase()) {
            case 'high': return { color: '#ef4444', backgroundColor: '#fef2f2', borderColor: '#fecaca' };
            case 'medium': return { color: '#f59e0b', backgroundColor: '#fffbeb', borderColor: '#fde68a' };
            default: return { color: '#10b981', backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' };
        }
    };

    const renderList = (items) => {
        if (!items) return null;
        if (typeof items === 'string') return <li>{items}</li>;
        if (Array.isArray(items)) {
            return items.map((item, index) => <li key={index}>{item}</li>);
        }
        // Handle object case
        if (typeof items === 'object') {
            return Object.values(items).map((item, index) => <li key={index}>{item}</li>);
        }
        return null;
    };

    const downloadReport = async () => {
        try {
            const payload = {
                feedback: suggestionData?.feedback_text || '',
                sentiment: suggestionData?.sentiment_label || '',
                suggestion: JSON.stringify(normalized)
            };

            const res = await fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:5000'}/generate-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error('Failed to generate report');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Feedback_Report.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Error downloading report', err);
            alert('Could not download report. Please try again.');
        }
    };

    return (
        <div style={{ marginTop: '24px' }}>
            {/* Download button - appears when suggestionData exists and we have valid normalized data */}
            {normalized && (normalized.type === 'basic' || normalized.type === 'advanced' || normalized.title) && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                    <button
                        type="button"
                        onClick={downloadReport}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                        Download Personalized Report
                    </button>
                </div>
            )}
            {/* Main suggestion card (dark glassy theme) */}
            <div style={{
                border: '1px solid rgba(148,163,184,0.15)',
                borderRadius: '16px',
                padding: '24px',
                backgroundColor: 'rgba(15,23,42,0.65)', // slate-900 with alpha
                backdropFilter: 'blur(10px) saturate(120%)',
                boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                marginBottom: '16px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                    <span style={{ fontSize: '24px', marginRight: '12px' }}>🎯</span>
                    <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: '#60a5fa' }}>AI Development Plan</h3>
                        <p style={{ fontSize: '14px', color: '#cbd5e1' }}>
                            Focus: <span style={{ textTransform: 'capitalize', fontWeight: '500', color: '#93c5fd' }}>
                                {normalized.primary_focus?.replace(/_/g, ' ')}
                            </span>
                        </p>
                    </div>
                    <div style={{
                        padding: '8px 12px',
                        borderRadius: '9999px',
                        fontSize: '14px',
                        fontWeight: '500',
                        border: '1px solid',
                        ...getUrgencyColor(normalized.urgency)
                    }}>
                        {normalized.urgency} priority
                    </div>
                </div>

                {/* AI Confidence indicator (dark) */}
                <div style={{
                    backgroundColor: 'rgba(2,6,23,0.45)',
                    border: '1px solid rgba(148,163,184,0.12)',
                    padding: '12px',
                    borderRadius: '10px',
                    marginBottom: '16px'
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '14px',
                        marginBottom: '8px'
                    }}>
                        <span style={{ color: '#64748b' }}>AI Analysis Confidence</span>
                        <span style={{ color: '#1e40af', fontWeight: 'bold' }}>
                            {Math.round((normalized.confidence_score || 0.5) * 100)}%
                        </span>
                    </div>
                    <div style={{
                        width: '100%',
                        backgroundColor: 'rgba(30,41,59,0.7)',
                        borderRadius: '9999px',
                        height: '8px'
                    }}>
                        <div style={{
                            backgroundColor: '#1e40af',
                            height: '8px',
                            borderRadius: '9999px',
                            width: `${Math.round((normalized.confidence_score || 0.5) * 100)}%`,
                            transition: 'width 0.5s ease'
                        }}></div>
                    </div>
                </div>
            </div>

            {/* Suggestions in Brief - Quick Summary with dark glassy theme */}
            <div style={{
                border: '1px solid rgba(148,163,184,0.15)',
                borderRadius: '16px',
                padding: '24px',
                backgroundColor: 'rgba(15,23,42,0.65)',
                backdropFilter: 'blur(10px) saturate(120%)',
                boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                marginBottom: '16px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
                    <span style={{ fontSize: '24px', marginRight: '12px' }}>📝</span>
                    <h4 style={{ fontSize: '20px', fontWeight: 'bold', color: '#60a5fa', margin: 0 }}>
                        Suggestions in Brief
                    </h4>
                </div>

                <div style={{ display: 'grid', gap: '12px' }}>
                    {/* Primary Focus */}
                    {normalized.primary_focus && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            backgroundColor: 'rgba(30,58,138,0.25)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(96,165,250,0.3)'
                        }}>
                            <span style={{ fontSize: '20px', marginRight: '12px', marginTop: '2px' }}>🎯</span>
                            <div style={{ flex: 1 }}>
                                <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>Focus Area: </span>
                                <span style={{ color: '#e5e7eb', fontSize: '14px' }}>
                                    {normalized.primary_focus?.replace(/_/g, ' ').split(' ').map(word =>
                                        word.charAt(0).toUpperCase() + word.slice(1)
                                    ).join(' ')}
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Title/Plan Name */}
                    {normalized.title && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            backgroundColor: 'rgba(30,58,138,0.25)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(96,165,250,0.3)'
                        }}>
                            <span style={{ fontSize: '20px', marginRight: '12px', marginTop: '2px' }}>📋</span>
                            <div style={{ flex: 1 }}>
                                <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>Development Plan: </span>
                                <span style={{ color: '#e5e7eb', fontSize: '14px' }}>{normalized.title}</span>
                            </div>
                        </div>
                    )}

                    {/* Key Actions Summary */}
                    {normalized.immediate_actions && Array.isArray(normalized.immediate_actions) && normalized.immediate_actions.length > 0 && (
                        <div style={{
                            backgroundColor: 'rgba(30,58,138,0.25)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(96,165,250,0.3)'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                                <span style={{ fontSize: '20px', marginRight: '12px' }}>✨</span>
                                <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>
                                    Top 3 Actions to Take:
                                </span>
                            </div>
                            <ul style={{ margin: '0', paddingLeft: '32px', color: '#cbd5e1', fontSize: '14px', lineHeight: '1.8' }}>
                                {normalized.immediate_actions.slice(0, 3).map((action, index) => {
                                    // Extract only the first sentence
                                    const firstSentence = action.split(/[.!?]/)[0] + '.';
                                    return (
                                        <li key={index} style={{ marginBottom: index < 2 ? '6px' : '0' }}>
                                            {firstSentence}
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    )}

                    {/* Success Metrics Summary */}
                    {normalized.success_metrics && Array.isArray(normalized.success_metrics) && normalized.success_metrics.length > 0 && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            backgroundColor: 'rgba(30,58,138,0.25)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(96,165,250,0.3)'
                        }}>
                            <span style={{ fontSize: '20px', marginRight: '12px', marginTop: '2px' }}>📊</span>
                            <div style={{ flex: 1 }}>
                                <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>Key Metric: </span>
                                <span style={{ color: '#e5e7eb', fontSize: '14px' }}>
                                    {normalized.success_metrics[0]}
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Timeline */}
                    {normalized.timeline && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            backgroundColor: 'rgba(30,58,138,0.25)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(96,165,250,0.3)'
                        }}>
                            <span style={{ fontSize: '20px', marginRight: '12px', marginTop: '2px' }}>⏰</span>
                            <div style={{ flex: 1 }}>
                                <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>Timeline: </span>
                                <span style={{ color: '#e5e7eb', fontSize: '14px' }}>{normalized.timeline}</span>
                            </div>
                        </div>
                    )}

                    {/* Pattern Insights (if available) */}
                    {normalized.pattern_insights && normalized.pattern_insights.trend && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            backgroundColor: 'rgba(120,53,15,0.3)',
                            padding: '12px 16px',
                            borderRadius: '10px',
                            border: '1px solid rgba(251,191,36,0.4)'
                        }}>
                            <span style={{ fontSize: '20px', marginRight: '12px', marginTop: '2px' }}>💡</span>
                            <div style={{ flex: 1 }}>
                                <span style={{ fontWeight: '600', color: '#fcd34d', fontSize: '14px' }}>Pattern Insight: </span>
                                <span style={{ color: '#fef3c7', fontSize: '14px' }}>
                                    {normalized.pattern_insights.trend}
                                    {normalized.pattern_insights.recurring_themes &&
                                        Array.isArray(normalized.pattern_insights.recurring_themes) &&
                                        normalized.pattern_insights.recurring_themes.length > 0 &&
                                        ` - Recurring: ${normalized.pattern_insights.recurring_themes.join(', ').replace(/_/g, ' ')}`
                                    }
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Quick tip at bottom */}
                <div style={{
                    marginTop: '16px',
                    padding: '10px 16px',
                    backgroundColor: 'rgba(30,58,138,0.3)',
                    border: '1px solid rgba(96,165,250,0.2)',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#93c5fd',
                    textAlign: 'center',
                    fontStyle: 'italic'
                }}>
                    💡 Expand sections below for detailed weekly plans, resources, and metrics
                </div>
            </div>

            {/* Immediate Actions - Always visible with dark theme */}
            {normalized.immediate_actions && Array.isArray(normalized.immediate_actions) && normalized.immediate_actions.length > 0 && (
                <div style={{
                    border: '1px solid rgba(148,163,184,0.15)',
                    borderRadius: '16px',
                    padding: '24px',
                    backgroundColor: 'rgba(15,23,42,0.65)',
                    backdropFilter: 'blur(10px) saturate(120%)',
                    boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                    marginBottom: '16px'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                        <span style={{ fontSize: '24px', marginRight: '12px' }}>🚀</span>
                        <h4 style={{ fontSize: '20px', fontWeight: 'bold', color: '#60a5fa' }}>Start Today</h4>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {normalized.immediate_actions.slice(0, 3).map((action, index) => (
                            <div key={index} style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                backgroundColor: 'rgba(30,58,138,0.25)',
                                padding: '14px 16px',
                                borderRadius: '10px',
                                border: '1px solid rgba(96,165,250,0.3)'
                            }}>
                                <span style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: '28px',
                                    height: '28px',
                                    backgroundColor: '#1e40af',
                                    color: 'white',
                                    borderRadius: '50%',
                                    fontSize: '14px',
                                    fontWeight: 'bold',
                                    marginRight: '14px',
                                    marginTop: '2px',
                                    flexShrink: 0
                                }}>
                                    {index + 1}
                                </span>
                                <span style={{ color: '#cbd5e1', lineHeight: '1.6', fontSize: '14px' }}>
                                    {action}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Expandable sections with dark theme */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Weekly Goals */}
                {normalized.weekly_goals && Array.isArray(normalized.weekly_goals) && normalized.weekly_goals.length > 0 && (
                    <div style={{
                        border: '1px solid rgba(148,163,184,0.15)',
                        borderRadius: '16px',
                        backgroundColor: 'rgba(15,23,42,0.65)',
                        backdropFilter: 'blur(10px) saturate(120%)',
                        boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                        overflow: 'hidden'
                    }}>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                toggleSection('weekly');
                            }}
                            style={{
                                width: '100%',
                                padding: '18px 24px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                backgroundColor: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                fontSize: '16px',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(30,58,138,0.2)'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <span style={{ fontSize: '24px', marginRight: '12px' }}>📅</span>
                                <span style={{ fontWeight: '600', color: '#e5e7eb' }}>6-Week Development Plan</span>
                                <span style={{ fontSize: '14px', color: '#94a3b8', marginLeft: '12px' }}>
                                    Click to see weekly goals
                                </span>
                            </div>
                            <span style={{ color: '#60a5fa', fontSize: '20px' }}>
                                {expandedSection === 'weekly' ? '▼' : '▶'}
                            </span>
                        </button>
                        {expandedSection === 'weekly' && (
                            <div style={{
                                padding: '20px 24px',
                                borderTop: '1px solid rgba(148,163,184,0.15)',
                                backgroundColor: 'rgba(2,6,23,0.45)'
                            }}>
                                {normalized.weekly_goals.map((goal, index) => (
                                    <div key={index} style={{
                                        backgroundColor: 'rgba(30,58,138,0.25)',
                                        padding: '14px 16px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(96,165,250,0.3)',
                                        marginBottom: index < normalized.weekly_goals.length - 1 ? '12px' : '0'
                                    }}>
                                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                                            <span style={{
                                                backgroundColor: '#1e40af',
                                                color: 'white',
                                                borderRadius: '50%',
                                                width: '28px',
                                                height: '28px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '14px',
                                                fontWeight: 'bold',
                                                marginRight: '12px'
                                            }}>
                                                {index + 1}
                                            </span>
                                            <span style={{ fontWeight: '600', color: '#93c5fd', fontSize: '14px' }}>
                                                {goal.split(':')[0]}
                                            </span>
                                        </div>
                                        <p style={{ color: '#cbd5e1', fontSize: '14px', marginLeft: '40px', margin: '0' }}>
                                            {goal.split(':').slice(1).join(':').trim()}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Resources */}
                {normalized.resources && Array.isArray(normalized.resources) && normalized.resources.length > 0 && (
                    <div style={{
                        border: '1px solid rgba(148,163,184,0.15)',
                        borderRadius: '16px',
                        backgroundColor: 'rgba(15,23,42,0.65)',
                        backdropFilter: 'blur(10px) saturate(120%)',
                        boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                        overflow: 'hidden'
                    }}>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                toggleSection('resources');
                            }}
                            style={{
                                width: '100%',
                                padding: '18px 24px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                backgroundColor: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                fontSize: '16px',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(30,58,138,0.2)'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <span style={{ fontSize: '24px', marginRight: '12px' }}>📚</span>
                                <span style={{ fontWeight: '600', color: '#e5e7eb' }}>Learning Resources</span>
                                <span style={{ fontSize: '14px', color: '#94a3b8', marginLeft: '12px' }}>
                                    Books, courses, tools
                                </span>
                            </div>
                            <span style={{ color: '#60a5fa', fontSize: '20px' }}>
                                {expandedSection === 'resources' ? '▼' : '▶'}
                            </span>
                        </button>
                        {expandedSection === 'resources' && (
                            <div style={{
                                padding: '20px 24px',
                                borderTop: '1px solid rgba(148,163,184,0.15)',
                                backgroundColor: 'rgba(2,6,23,0.45)'
                            }}>
                                {normalized.resources.map((resource, index) => (
                                    <div key={index} style={{
                                        backgroundColor: 'rgba(30,58,138,0.25)',
                                        padding: '14px 16px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(96,165,250,0.3)',
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        marginBottom: index < normalized.resources.length - 1 ? '12px' : '0'
                                    }}>
                                        <span style={{ fontSize: '22px', marginRight: '14px', marginTop: '2px' }}>
                                            {resource.toLowerCase().includes('book') ? '📖' :
                                                resource.toLowerCase().includes('course') ? '🎓' :
                                                    resource.toLowerCase().includes('tool') ? '🛠️' : '💡'}
                                        </span>
                                        <div style={{ fontSize: '14px', flex: 1 }}>
                                            <span style={{ color: '#93c5fd', fontWeight: '600' }}>
                                                {resource.split(':')[0]}:
                                            </span>
                                            <span style={{ color: '#cbd5e1', marginLeft: '8px' }}>
                                                {resource.split(':').slice(1).join(':').trim()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Success Metrics */}
                {normalized.success_metrics && Array.isArray(normalized.success_metrics) && normalized.success_metrics.length > 0 && (
                    <div style={{
                        border: '1px solid rgba(148,163,184,0.15)',
                        borderRadius: '16px',
                        backgroundColor: 'rgba(15,23,42,0.65)',
                        backdropFilter: 'blur(10px) saturate(120%)',
                        boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                        overflow: 'hidden'
                    }}>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                toggleSection('metrics');
                            }}
                            style={{
                                width: '100%',
                                padding: '18px 24px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                backgroundColor: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                fontSize: '16px',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(30,58,138,0.2)'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <span style={{ fontSize: '24px', marginRight: '12px' }}>📊</span>
                                <span style={{ fontWeight: '600', color: '#e5e7eb' }}>Track Your Progress</span>
                                <span style={{ fontSize: '14px', color: '#94a3b8', marginLeft: '12px' }}>
                                    Measurable success metrics
                                </span>
                            </div>
                            <span style={{ color: '#60a5fa', fontSize: '20px' }}>
                                {expandedSection === 'metrics' ? '▼' : '▶'}
                            </span>
                        </button>
                        {expandedSection === 'metrics' && (
                            <div style={{
                                padding: '20px 24px',
                                borderTop: '1px solid rgba(148,163,184,0.15)',
                                backgroundColor: 'rgba(2,6,23,0.45)'
                            }}>
                                {normalized.success_metrics.map((metric, index) => (
                                    <div key={index} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '14px 16px',
                                        backgroundColor: 'rgba(16,185,129,0.15)',
                                        border: '1px solid rgba(52,211,153,0.3)',
                                        borderRadius: '10px',
                                        marginBottom: index < normalized.success_metrics.length - 1 ? '12px' : '0'
                                    }}>
                                        <span style={{ color: '#34d399', marginRight: '14px', fontSize: '22px' }}>📈</span>
                                        <span style={{ color: '#cbd5e1', fontSize: '14px', flex: 1 }}>{metric}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Timeline footer (dark glassy theme) */}
            <div style={{
                border: '1px solid rgba(148,163,184,0.12)',
                borderRadius: '16px',
                padding: '16px',
                backgroundColor: 'rgba(15,23,42,0.65)',
                backdropFilter: 'blur(10px) saturate(120%)',
                boxShadow: '0 10px 30px rgba(2,6,23,0.35)',
                marginTop: '16px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ color: '#93c5fd', marginRight: '8px' }}>⏰</span>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#e5e7eb' }}>
                        {normalized.timeline || "Begin within the next week"}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default SuggestionDisplay;
