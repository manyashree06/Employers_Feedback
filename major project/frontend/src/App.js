import React, { useState } from 'react';
import { DataProvider } from './context/DataContext';
import FeedbackForm from './components/FeedbackForm';
import AuroraBackground from './components/common/AuroraBackground';
import FeedbackList from './components/FeedbackList';
import Dashboard from './components/Dashboard';
import DistributionChart from './components/DistributionChart';
import TrendChart from './components/TrendChart';

function App() {
    const [activeSection, setActiveSection] = useState('dashboard');
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [feedbackRefreshTrigger, setFeedbackRefreshTrigger] = useState(0);

    // Function to trigger feedback list refresh
    const handleFeedbackSubmitted = (newFeedback) => {
        setFeedbackRefreshTrigger(prev => prev + 1);
        // Optionally switch to history tab to show the new feedback
        // setActiveSection('history');
    };

    const sections = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'feedback', label: 'Submit Feedback', icon: '💬' },
        { id: 'analytics', label: 'Analytics', icon: '📈' },
        { id: 'history', label: 'Feedback History', icon: '📋' }
    ];

    return (
        <DataProvider>
            {/* Background lives outside main stacking context so it applies to all pages */}
            <AuroraBackground />
            <div className="relative z-10 min-h-screen">
                {/* Navigation Header */}
                <nav className="fixed top-0 left-0 right-0 z-50 bg-neutral/80 backdrop-blur-lg border-b border-neutral-light/20">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex items-center justify-between h-16">
                            <div className="flex items-center space-x-4">
                                <div className="flex items-center space-x-2">
                                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                        <span className="text-white font-bold text-sm">EF</span>
                                    </div>
                                    <h1 className="text-xl font-bold text-primary">Feedback Analytics</h1>
                                </div>
                            </div>
                            <div className="hidden md:flex items-center space-x-1">
                                {sections.map((section) => (
                                    <button
                                        key={section.id}
                                        onClick={() => setActiveSection(section.id)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${activeSection === section.id
                                            ? 'bg-primary/20 text-primary shadow-lg'
                                            : 'text-text-secondary hover:text-text-primary hover:bg-neutral-light/20'
                                            }`}
                                    >
                                        <span className="mr-2">{section.icon}</span>
                                        {section.label}
                                    </button>
                                ))}
                            </div>
                            <div className="md:hidden flex items-center">
                                <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="text-text-secondary hover:text-text-primary">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                    {isMenuOpen && (
                        <div className="md:hidden">
                            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                                {sections.map((section) => (
                                    <button
                                        key={section.id}
                                        onClick={() => {
                                            setActiveSection(section.id);
                                            setIsMenuOpen(false);
                                        }}
                                        className={`block w-full text-left px-3 py-2 rounded-md text-base font-medium ${activeSection === section.id
                                            ? 'bg-primary/20 text-primary'
                                            : 'text-text-secondary hover:text-text-primary hover:bg-neutral-light/20'
                                            }`}
                                    >
                                        <span className="mr-2">{section.icon}</span>
                                        {section.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </nav>

                {/* Hero Section */}
                <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
                    <div className="max-w-7xl mx-auto text-center">
                        <div className="float">
                            <h1 className="text-5xl md:text-7xl font-bold mb-6">
                                <span className="text-primary">Employer Feedback</span>
                                <br />
                                <span className="text-text-primary">Analytics Platform</span>
                            </h1>
                            <p className="text-xl text-text-secondary max-w-3xl mx-auto mb-8 leading-relaxed">
                                Transform feedback into actionable insights with our advanced sentiment analysis and
                                comprehensive analytics dashboard. Make data-driven decisions for better outcomes.
                            </p>
                            <div className="flex flex-wrap justify-center gap-4">
                                <div className="card px-6 py-4">
                                    <div className="text-2xl font-bold text-primary">500+</div>
                                    <div className="text-sm text-text-secondary">Feedback Entries</div>
                                </div>
                                <div className="card px-6 py-4">
                                    <div className="text-2xl font-bold text-primary">95%</div>
                                    <div className="text-sm text-text-secondary">Accuracy Rate</div>
                                </div>
                                <div className="card px-6 py-4">
                                    <div className="text-2xl font-bold text-primary">24/7</div>
                                    <div className="text-sm text-text-secondary">Real-time Analysis</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Main Content */}
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
                    {activeSection === 'dashboard' && (
                        <div className="space-y-8">
                            <section className="card p-6 md:p-8 glow">
                                <h2 className="text-3xl font-bold text-primary mb-6">Quick Stats</h2>
                                <Dashboard />
                            </section>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <section className="card p-6">
                                    <DistributionChart />
                                </section>
                                <section className="card p-6">
                                    <TrendChart />
                                </section>
                            </div>
                        </div>
                    )}

                    {activeSection === 'feedback' && (
                        <section className="card p-6 md:p-8">
                            <h2 className="text-3xl font-bold text-primary mb-6 text-center">Submit Your Feedback</h2>
                            <FeedbackForm onFeedbackSubmitted={handleFeedbackSubmitted} />
                        </section>
                    )}

                    {activeSection === 'analytics' && (
                        <div className="space-y-8">
                            <section className="card p-6 md:p-8">
                                <h2 className="text-3xl font-bold text-primary mb-6">Sentiment Distribution</h2>
                                <DistributionChart />
                            </section>
                            <section className="card p-6 md:p-8">
                                <h2 className="text-3xl font-bold text-primary mb-6">Feedback Trend</h2>
                                <TrendChart />
                            </section>
                        </div>
                    )}

                    {activeSection === 'history' && (
                        <section className="card p-6 md:p-8">
                            <h2 className="text-3xl font-bold text-primary mb-6">Feedback History</h2>
                            <FeedbackList refreshTrigger={feedbackRefreshTrigger} />
                        </section>
                    )}
                </main>
            </div>
        </DataProvider>
    );
}

export default App;
