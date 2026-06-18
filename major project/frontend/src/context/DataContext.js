import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

const DataContext = createContext();

export const useData = () => {
    const context = useContext(DataContext);
    if (!context) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
};

export const DataProvider = ({ children }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [lastFetch, setLastFetch] = useState(0);

    // Cache duration: 5 minutes
    const CACHE_DURATION = 5 * 60 * 1000;

    const fetchStats = async (forceRefresh = false) => {
        const now = Date.now();

        // Return cached data if it's still fresh and not forcing refresh
        if (!forceRefresh && stats && (now - lastFetch < CACHE_DURATION)) {
            return stats;
        }

        setLoading(true);
        setError(null);

        try {
            const res = await axios.get(`${API_BASE}/api/dashboard_stats?source=dataset`, {
                timeout: 30000, // more forgiving: dataset computation can be heavy
            });
            setStats(res.data);
            setLastFetch(now);
            return res.data;
        } catch (err) {
            const code = err?.code;
            const msgFromServer = err?.response?.data?.error;
            const errorMessage = msgFromServer ||
                (code === 'ECONNABORTED' ? 'Request timeout - server may be slow' :
                    code === 'ECONNREFUSED' ? 'Cannot connect to server' :
                        'Failed to load data');
            setError(errorMessage);
            // Do NOT throw here — avoid React error overlay; return null gracefully
            return null;
        } finally {
            setLoading(false);
        }
    };

    // Auto-fetch on mount
    useEffect(() => {
        // Swallow any rejections to prevent unhandled promise rejection in dev overlay
        Promise.resolve(fetchStats()).catch(() => { });
    }, []);

    const refreshData = () => fetchStats(true);

    const value = {
        stats,
        loading,
        error,
        fetchStats,
        refreshData,
        isStale: stats && (Date.now() - lastFetch > CACHE_DURATION)
    };

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
};