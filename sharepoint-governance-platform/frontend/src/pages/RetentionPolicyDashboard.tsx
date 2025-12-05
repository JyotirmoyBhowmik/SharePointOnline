/**
 * Retention Policy Status Dashboard
 * ==================================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Dashboard for viewing retention policies, exclusions, and compliance status.
 *   Includes ability to request exclusions and approve/reject exclusion requests.
 */

import React, { useState, useEffect } from 'react';
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Tabs,
    Tab,
    IconButton,
    Tooltip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import AddIcon from '@mui/icons-material/Add';
import PolicyIcon from '@mui/icons-material/Policy';
import VerifiedIcon from '@mui/icons-material/Verified';
import api from '../services/api';

interface RetentionPolicy {
    id: string;
    name: string;
    retention_period_days: number;
    sites_count: number;
    compliance_percentage: number;
}

interface ExclusionRequest {
    id: string;
    site_name: string;
    policy_name: string;
    justification: string;
    requested_by: string;
    requested_at: string;
    status: 'pending' | 'approved' | 'rejected';
}

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
    return (
        <div role="tabpanel" hidden={value !== index}>
            {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
        </div>
    );
};

const RetentionPolicyDashboard: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [currentTab, setCurrentTab] = useState(0);
    const [policies, setPolicies] = useState<RetentionPolicy[]>([]);
    const [exclusions, setExclusions] = useState<ExclusionRequest[]>([]);
    const [requestDialogOpen, setRequestDialogOpen] = useState(false);
    const [selectedPolicyId, setSelectedPolicyId] = useState('');
    const [justification, setJustification] = useState('');

    useEffect(() => {
        fetchRetentionData();
    }, []);

    const fetchRetentionData = async () => {
        try {
            setLoading(true);
            const [policiesRes, exclusionsRes] = await Promise.all([
                api.get('/v2/retention/policies'),
                api.get('/v2/retention/exclusions'),
            ]);

            setPolicies(policiesRes.data.policies || []);
            setExclusions(exclusionsRes.data.exclusions || []);
        } catch (error) {
            console.error('Failed to fetch retention data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRequestExclusion = async () => {
        try {
            await api.post('/v2/retention/exclusions', {
                policy_id: selectedPolicyId,
                justification,
            });
            setRequestDialogOpen(false);
            setJustification('');
            await fetchRetentionData();
        } catch (error) {
            console.error('Failed to create exclusion request:', error);
        }
    };

    const handleApprove = async (exclusionId: string) => {
        try {
            await api.put(`/v2/retention/exclusions/${exclusionId}/approve`, {
                comments: 'Approved',
            });
            await fetchRetentionData();
        } catch (error) {
            console.error('Failed to approve exclusion:', error);
        }
    };

    const handleReject = async (exclusionId: string) => {
        try {
            await api.delete(`/v2/retention/exclusions/${exclusionId}`);
            await fetchRetentionData();
        } catch (error) {
            console.error('Failed to reject exclusion:', error);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    // Calculate overall compliance
    const overallCompliance =
        policies.length > 0
            ? policies.reduce((sum, p) => sum + p.compliance_percentage, 0) / policies.length
            : 0;

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {/* Page Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
                        Retention Policy Management
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Monitor retention policies, exclusions, and compliance status
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setRequestDialogOpen(true)}
                >
                    Request Exclusion
                </Button>
            </Box>

            {/* Summary Cards */}
            <Grid container spacing={3} mb={4}>
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={1}>
                            <PolicyIcon sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="h6">Active Policies</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="primary">
                            {policies.length}
                        </Typography>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={1}>
                            <VerifiedIcon sx={{ mr: 1, color: 'success.main' }} />
                            <Typography variant="h6">Overall Compliance</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="success.main">
                            {overallCompliance.toFixed(1)}%
                        </Typography>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={1}>
                            <CancelIcon sx={{ mr: 1, color: 'warning.main' }} />
                            <Typography variant="h6">Pending Exclusions</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="warning.main">
                            {exclusions.filter((e) => e.status === 'pending').length}
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)}>
                    <Tab label="Policies" />
                    <Tab label="Exclusion Requests" />
                    <Tab label="Compliance Report" />
                </Tabs>

                {/* Policies Tab */}
                <TabPanel value={currentTab} index={0}>
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Policy Name</TableCell>
                                    <TableCell align="right">Retention Period</TableCell>
                                    <TableCell align="right">Sites Affected</TableCell>
                                    <TableCell align="right">Compliance</TableCell>
                                    <TableCell>Status</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {policies.map((policy) => (
                                    <TableRow key={policy.id}>
                                        <TableCell>
                                            <Typography fontWeight={600}>{policy.name}</Typography>
                                        </TableCell>
                                        <TableCell align="right">{policy.retention_period_days} days</TableCell>
                                        <TableCell align="right">{policy.sites_count}</TableCell>
                                        <TableCell align="right">
                                            <Chip
                                                label={`${policy.compliance_percentage.toFixed(1)}%`}
                                                color={
                                                    policy.compliance_percentage >= 90
                                                        ? 'success'
                                                        : policy.compliance_percentage >= 70
                                                            ? 'warning'
                                                            : 'error'
                                                }
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Chip label="Active" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </TabPanel>

                {/* Exclusions Tab */}
                <TabPanel value={currentTab} index={1}>
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Site</TableCell>
                                    <TableCell>Policy</TableCell>
                                    <TableCell>Justification</TableCell>
                                    <TableCell>Requested By</TableCell>
                                    <TableCell>Date</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell align="center">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {exclusions.map((exclusion) => (
                                    <TableRow key={exclusion.id}>
                                        <TableCell>{exclusion.site_name}</TableCell>
                                        <TableCell>{exclusion.policy_name}</TableCell>
                                        <TableCell>
                                            <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                                                {exclusion.justification}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>{exclusion.requested_by}</TableCell>
                                        <TableCell>
                                            {new Date(exclusion.requested_at).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={exclusion.status}
                                                color={
                                                    exclusion.status === 'approved'
                                                        ? 'success'
                                                        : exclusion.status === 'rejected'
                                                            ? 'error'
                                                            : 'warning'
                                                }
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell align="center">
                                            {exclusion.status === 'pending' && (
                                                <Box display="flex" gap={1} justifyContent="center">
                                                    <Tooltip title="Approve">
                                                        <IconButton
                                                            size="small"
                                                            color="success"
                                                            onClick={() => handleApprove(exclusion.id)}
                                                        >
                                                            <CheckCircleIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                    <Tooltip title="Reject">
                                                        <IconButton
                                                            size="small"
                                                            color="error"
                                                            onClick={() => handleReject(exclusion.id)}
                                                        >
                                                            <CancelIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                </Box>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </TabPanel>

                {/* Compliance Report Tab */}
                <TabPanel value={currentTab} index={2}>
                    <Typography variant="body1" color="text.secondary">
                        Detailed compliance reports and metrics will be displayed here
                    </Typography>
                </TabPanel>
            </Paper>

            {/* Request Exclusion Dialog */}
            <Dialog
                open={requestDialogOpen}
                onClose={() => setRequestDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>Request Retention Policy Exclusion</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            select
                            fullWidth
                            label="Select Policy"
                            value={selectedPolicyId}
                            onChange={(e) => setSelectedPolicyId(e.target.value)}
                            SelectProps={{ native: true }}
                            sx={{ mb: 2 }}
                        >
                            <option value="">-- Select Policy --</option>
                            {policies.map((policy) => (
                                <option key={policy.id} value={policy.id}>
                                    {policy.name}
                                </option>
                            ))}
                        </TextField>
                        <TextField
                            fullWidth
                            multiline
                            rows={4}
                            label="Business Justification"
                            value={justification}
                            onChange={(e) => setJustification(e.target.value)}
                            helperText="Provide a detailed business justification for this exclusion request"
                            placeholder="Enter justification..."
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRequestDialogOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={handleRequestExclusion}
                        disabled={!selectedPolicyId || !justification.trim()}
                    >
                        Submit Request
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default RetentionPolicyDashboard;
