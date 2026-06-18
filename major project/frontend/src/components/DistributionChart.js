import React from 'react';
import { useData } from '../context/DataContext';
import { LoadingSpinner, ErrorDisplay, NoDataDisplay } from './common/LoadingComponents';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

function DistributionChart() {
    const { stats, loading, error, refreshData } = useData();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 md:h-80">
                <LoadingSpinner text="Loading distribution chart..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-64 md:h-80">
                <ErrorDisplay error={error} onRetry={refreshData} />
            </div>
        );
    }

    if (!stats || stats.total === 0) {
        return (
            <div className="flex items-center justify-center h-64 md:h-80">
                <NoDataDisplay message="No sentiment data to display" />
            </div>
        );
    }

    const pieData = {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [
            {
                label: 'Count',
                data: [
                    stats.count_positive || 0,
                    stats.count_neutral || 0,
                    stats.count_negative || 0
                ],
                backgroundColor: ['rgba(16, 185, 129, 0.7)', 'rgba(245, 158, 11, 0.7)', 'rgba(239, 68, 68, 0.7)'],
                borderColor: ['#10B981', '#F59E0B', '#EF4444'],
                borderWidth: 1,
            },
        ],
    };

    const options = {
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: '#9CA3AF',
                    font: {
                        size: 14,
                    },
                },
            },
        },
    };

    return (
        <div className="h-64 md:h-80">
            <Pie data={pieData} options={options} />
        </div>
    );
}

export default DistributionChart;


