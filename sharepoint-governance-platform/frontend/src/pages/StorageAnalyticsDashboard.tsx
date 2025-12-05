/**
 * Storage Analytics Visualization Dashboard
 * =========================================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Comprehensive storage analytics dashboard with charts and visualizations.
 *   Displays storage summary, trends, top consumers, and recommendations.
 */

import React, { useState, useEffect } from 'react';
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    CircularProgress,
    Card,
    CardContent,
    List,
    ListItem,
    ListItemText,
    Chip,
} from '@mui/material';
import {
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import WarningIcon from '@mui/icons-material/Warning';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import api from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

interface StorageSummary {
    total_storage_gb: number;
    total_quota_gb: number;
    usage_percentage: number;
    sites_over_90_percent: number;
    top_consumers: Array<{
        site_id: string;
        name: string;
        storage_used_gb: number;
    }>;
}

const StorageAnalyticsDashboard: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [summary, setSummary] = useState<StorageSummary | null>(null);
    const [trends, setTrends] = useState<any[]>([]);
    const [recommendations, setRecommendations] = useState<any[]>([]);

    useEffect(() => {
        fetchStorageData();
    }, []);

    const fetchStorageData = async () => {
        try {
            setLoading(true);
            const [summaryRes, trendsRes, recsRes] = await Promise.all([
                api.get('/v2/storage/summary'),
                api.get('/v2/storage/trends'),
                api.get('/v2/storage/recommendations'),
            ]);

            setSummary(summaryRes.data);
            setTrends(trendsRes.data.trends || []);
            setRecommendations(recsRes.data.recommendations || []);
        } catch (error) {
            console.error('Failed to fetch storage data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    // Prepare data for pie chart
    const pieData = summary
        ? [
            { name: 'Used', value: summary.total_storage_gb },
            {
                name: 'Available',
                value: summary.total_quota_gb - summary.total_storage_gb,
            },
        ]
        : [];

    // Prepare data for bar chart (top consumers)
    const barData =
        summary?.top_consumers.map((site) => ({
            name: site.name.substring(0, 20) + '...',
            storage: site.storage_used_gb,
        })) || [];

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {/* Page Header */}
            <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
                Storage Analytics
            </Typography>
            <Typography variant="body1" color="text.secondary" mb={4}>
                Comprehensive storage usage analysis and recommendations
            </Typography>

            <Grid container spacing={3}>
                {/* Storage Summary Cards */}
                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" variant="subtitle2">
                                Total Storage
                            </Typography>
                            <Typography variant="h5" fontWeight={700} color="primary">
                                {summary?.total_storage_gb.toFixed(2)} GB
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                of {summary?.total_quota_gb.toFixed(2)} GB
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" variant="subtitle2">
                                Usage Percentage
                            </Typography>
                            <Typography variant="h5" fontWeight={700} color="success.main">
                                {summary?.usage_percentage.toFixed(1)}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" variant="subtitle2">
                                Sites Over 90%
                            </Typography>
                            <Typography variant="h5" fontWeight={700} color="error">
                                {summary?.sites_over_90_percent || 0}
                            </Typography>
                            <Chip
                                label="Action Needed"
                                size="small"
                                color="error"
                                icon={<WarningIcon />}
                            />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" variant="subtitle2">
                                Growth Trend
                            </Typography>
                            <Box display="flex" alignItems="center">
                                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                                <Typography variant="h5" fontWeight={700}>
                                    +12%
                                </Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                                vs last month
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Storage Distribution Pie Chart */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '400px' }}>
                        <Typography variant="h6" gutterBottom>
                            Storage Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height="90%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) =>
                                        `${name}: ${(percent * 100).toFixed(1)}%`
                                    }
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                {/* Storage Trends Line Chart */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '400px' }}>
                        <Typography variant="h6" gutterBottom>
                            Storage Trends (Last 6 Months)
                        </Typography>
                        <ResponsiveContainer width="100%" height="90%">
                            <LineChart data={trends}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis label={{ value: 'GB', angle: -90, position: 'insideLeft' }} />
                                <Tooltip />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="storage_gb"
                                    stroke="#8884d8"
                                    name="Storage Used"
                                    strokeWidth={2}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                {/* Top Storage Consumers */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3, height: '400px' }}>
                        <Typography variant="h6" gutterBottom>
                            Top Storage Consumers
                        </Typography>
                        <ResponsiveContainer width="100%" height="90%">
                            <BarChart data={barData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                                <YAxis label={{ value: 'GB', angle: -90, position: 'insideLeft' }} />
                                <Tooltip />
                                <Bar dataKey="storage" fill="#0088FE" />
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                {/* Recommendations */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, height: '400px', overflow: 'auto' }}>
                        <Typography variant="h6" gutterBottom>
                            Recommendations
                        </Typography>
                        <List>
                            {recommendations.map((rec, index) => (
                                <ListItem key={index} divider>
                                    <ListItemText
                                        primary={rec.title}
                                        secondary={rec.description}
                                        primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                                        secondaryTypographyProps={{ variant: 'caption' }}
                                    />
                                </ListItem>
                            ))}
                            {recommendations.length === 0 && (
                                <Typography variant="body2" color="text.secondary">
                                    No recommendations at this time
                                </Typography>
                            )}
                        </List>
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default StorageAnalyticsDashboard;
