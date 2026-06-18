import React from 'react';

const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12'
    };

    return (
        <div className="flex flex-col items-center justify-center space-y-3">
            <div className={`animate-spin rounded-full border-b-2 border-primary ${sizeClasses[size]}`}></div>
            <span className="text-text-secondary text-sm">{text}</span>
        </div>
    );
};

const ErrorDisplay = ({ error, onRetry, retryText = 'Retry' }) => {
    return (
        <div className="text-center py-8">
            <div className="text-red-400 mb-4 flex items-center justify-center">
                <span className="mr-2 text-xl">⚠️</span>
                <span>{error}</span>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
                >
                    {retryText}
                </button>
            )}
        </div>
    );
};

const NoDataDisplay = ({ message = 'No data available' }) => {
    return (
        <div className="text-center py-8 text-text-secondary">
            <div className="text-4xl mb-2">📊</div>
            <div>{message}</div>
        </div>
    );
};

export { LoadingSpinner, ErrorDisplay, NoDataDisplay };