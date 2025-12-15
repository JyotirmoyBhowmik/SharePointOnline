/**
 * Live Metrics Dashboard
 * ======================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Dashboard page displaying real-time metrics for SharePoint governance.
 *   Shows key metrics like total sites, pending reviews, storage usage, and anomalies.
 */

import React, { FC } from 'react';
import Grid from '@mui/material/Grid';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import MetricWidget from '../components/MetricWidget';
import StorageIcon from '@mui/icons-material/Storage';
import AssignmentIcon from '@mui/icons-material/Assignment';
import WarningIcon from '@mui/icons-material/Warning';
import CloudIcon from '@mui/icons-material/Cloud';
import api from '../services/api';

const LiveMetricsDashboard: FC = () => {
    // Fetch functions for each metric
    const fetchTotalSites = async (): Promise<number> => {
        const response = await api.get('/v1/dashboard/overview');
        return response.data.total_sites || 0;
    };

    const fetchPendingReviews = async (): Promise<number> => {
        const response = await api.get('/v1/dashboard/overview');
        return response.data.pending_reviews || 0;
    };

    const fetchStorageUsage = async (): Promise<string> => {
        const response = await api.get('/v2/storage/summary');
        return `${response.data.usage_percentage || 0}%`;
    };

    const fetchAnomalies = async (): Promise<number> => {
        const response = await api.get('/v3/analytics/anomalies?days=7');
        return response.data.total || 0;
    };

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {/* Page Header */}
            <Box mb={4}>
                <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
                    Dashboard Overview
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Real-time metrics updated every 30 seconds
                </Typography>
            </Box>

            {/* Metrics Grid */}
            <Grid container spacing={3}>
                {/* Total Sites */}
                <Grid item xs={12} sm={6} md={3}>
                    <MetricWidget
                        title="Total Sites"
                        value={0}
                        icon={<CloudIcon fontSize="large" />}
                        fetchData={fetchTotalSites}
                        color="primary"
                        trend={{ direction: 'up', value: 5 }}
                    />
                </Grid>

                {/* Pending Reviews */}
                <Grid item xs={12} sm={6} md={3}>
                    <MetricWidget
                        title="Pending Reviews"
                        value={0}
                        icon={<AssignmentIcon fontSize="large" />}
                        fetchData={fetchPendingReviews}
                        color="warning"
                    />
                </Grid>

                {/* Storage Usage */}
                <Grid item xs={12} sm={6} md={3}>
                    <MetricWidget
                        title="Storage Usage"
                        value="0%"
                        unit="of quota"
                        icon={<StorageIcon fontSize="large" />}
                        fetchData={fetchStorageUsage}
                        color="success"
                        trend={{ direction: 'up', value: 12 }}
                    />
                </Grid>

                {/* Anomalies Detected */}
                <Grid item xs={12} sm={6} md={3}>
                    <MetricWidget
                        title="Anomalies (7 days)"
                        value={0}
                        icon={<WarningIcon fontSize="large" />}
                        fetchData={fetchAnomalies}
                        color="error"
                    />
                </Grid>
            </Grid>
        </Container>
    );
};

export default LiveMetricsDashboard;
