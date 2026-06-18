import React from 'react';
import { useData } from '../context/DataContext';
import { LoadingSpinner, ErrorDisplay, NoDataDisplay } from './common/LoadingComponents';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

function TrendChart() {
    const { stats, loading, error, refreshData } = useData();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 md:h-80">
                <LoadingSpinner text="Loading trend chart..." />
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

    if (!stats || !stats.timeseries || stats.timeseries.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 md:h-80">
                <NoDataDisplay message="No trend data available" />
            </div>
        );
    }

    const labels = stats.timeseries.map((p) => p.date);

    const avgData = {
        labels,
        datasets: [
            {
                label: 'Average Sentiment',
                data: stats.timeseries.map((p) => p.avg_score),
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2,
                pointBackgroundColor: '#3B82F6',
            },
        ],
    };

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                intersect: false,
                mode: 'index',
            },
        },
        scales: {
            x: {
                ticks: { color: '#9CA3AF' },
                grid: { color: 'rgba(75, 85, 99, 0.3)' },
            },
            y: {
                ticks: { color: '#9CA3AF' },
                grid: { color: 'rgba(75, 85, 99, 0.3)' },
            },
        },
    };

    const avgOptions = {
        ...commonOptions,
        scales: {
            ...commonOptions.scales,
            y: { ...commonOptions.scales.y, min: -1, max: 1 },
        },
    };

    const countData = {
        labels,
        datasets: [
            {
                label: 'Feedback Count',
                data: stats.timeseries.map((p) => p.count),
                backgroundColor: 'rgba(16, 185, 129, 0.6)',
                borderColor: '#10B981',
                borderWidth: 1,
            },
        ],
    };

    const countOptions = {
        ...commonOptions,
        scales: {
            ...commonOptions.scales,
            y: { ...commonOptions.scales.y, beginAtZero: true },
        },
    };

    return (
        <div className="grid grid-cols-1 gap-8">
            <div>
                <h3 className="text-lg font-semibold mb-4 text-text-primary">Average Sentiment Over Time</h3>
                <div className="h-64 md:h-80">
                    <Line data={avgData} options={avgOptions} />
                </div>
            </div>
            <div>
                <h3 className="text-lg font-semibold mb-4 text-text-primary">Feedback Count Over Time</h3>
                <div className="h-64 md:h-80">
                    <Bar data={countData} options={countOptions} />
                </div>
            </div>
        </div>
    );
}

export default TrendChart;


