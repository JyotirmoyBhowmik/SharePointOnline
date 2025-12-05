/**
 * Real-Time Metrics Widget Component
 * ==================================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Dashboard metric card component that displays live statistics with auto-refresh.
 *   Supports different metric types (number, percentage, trend) and update intervals.
 * 
 * Features:
 *   - Auto-refresh every 30 seconds
 *   - Loading and error states
 *   - Responsive design
 *   - Icon support
 *   - Trend indicator (up/down)
 */

import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    CircularProgress,
    Chip,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

interface MetricWidgetProps {
    title: string;
    value: number | string;
    unit?: string;
    icon?: React.ReactElement;
    trend?: {
        direction: 'up' | 'down';
        value: number;
    };
    refreshInterval?: number; // Milliseconds
    fetchData: () => Promise<number | string>;
    color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
}

const MetricWidget: React.FC<MetricWidgetProps> = ({
    title,
    value: initialValue,
    unit = '',
    icon,
    trend,
    refreshInterval = 30000, // 30 seconds default
    fetchData,
    color = 'primary',
}) => {
    const [value, setValue] = useState(initialValue);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Auto-refresh data
    useEffect(() => {
        const refreshData = async () => {
            try {
                setLoading(true);
                const newValue = await fetchData();
                setValue(newValue);
                setError(null);
            } catch (err) {
                setError('Failed to load data');
                console.error('Metric fetch error:', err);
            } finally {
                setLoading(false);
            }
        };

        // Initial fetch
        refreshData();

        // Set up interval for auto-refresh
        const interval = setInterval(refreshData, refreshInterval);

        // Cleanup
        return () => clearInterval(interval);
    }, [fetchData, refreshInterval]);

    return (
        <Card
            sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                },
            }}
        >
            <CardContent>
                {/* Header with icon */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography color="text.secondary" variant="subtitle2" fontWeight={600}>
                        {title}
                    </Typography>
                    {icon && (
                        <Box
                            sx={{
                                color: `${color}.main`,
                                display: 'flex',
                                alignItems: 'center',
                            }}
                        >
                            {icon}
                        </Box>
                    )}
                </Box>

                {/* Main value */}
                <Box display="flex" alignItems="baseline" mb={1}>
                    {loading ? (
                        <CircularProgress size={24} />
                    ) : error ? (
                        <Typography color="error" variant="body2">
                            {error}
                        </Typography>
                    ) : (
                        <>
                            <Typography variant="h4" component="div" fontWeight={700} color={`${color}.main`}>
                                {typeof value === 'number' ? value.toLocaleString() : value}
                            </Typography>
                            {unit && (
                                <Typography variant="body1" color="text.secondary" ml={1}>
                                    {unit}
                                </Typography>
                            )}
                        </>
                    )}
                </Box>

                {/* Trend indicator */}
                {trend && !loading && !error && (
                    <Box display="flex" alignItems="center">
                        <Chip
                            size="small"
                            icon={
                                trend.direction === 'up' ? (
                                    <TrendingUpIcon fontSize="small" />
                                ) : (
                                    <TrendingDownIcon fontSize="small" />
                                )
                            }
                            label={`${trend.value}%`}
                            color={trend.direction === 'up' ? 'success' : 'error'}
                            sx={{ fontWeight: 600 }}
                        />
                        <Typography variant="caption" color="text.secondary" ml={1}>
                            vs last month
                        </Typography>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default MetricWidget;
