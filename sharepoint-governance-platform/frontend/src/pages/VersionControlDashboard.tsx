/**
 * Version Control Dashboard
 * =========================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Dashboard for managing SharePoint document library versions.
 *   Displays version statistics, cleanup recommendations, and provides cleanup wizard.
 */
/* eslint-disable */

import React, { useState, useEffect } from 'react';
import {
    Container,
    Grid,
    Paper,
    Typography,
    Box,
    Button,
    CircularProgress,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Stepper,
    Step,
    StepLabel,
    Alert,
} from '@mui/material';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import StorageIcon from '@mui/icons-material/Storage';
import RecommendIcon from '@mui/icons-material/Recommend';
import api from '../services/api';

interface Library {
    id: string;
    name: string;
    site_name: string;
    total_versions: number;
    storage_mb: number;
    potential_savings_mb: number;
}

const CLEANUP_STEPS = ['Select Libraries', 'Configure Settings', 'Review & Execute'];

const VersionControlDashboard: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [libraries, setLibraries] = useState<Library[]>([]);
    const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);
    const [activeStep, setActiveStep] = useState(0);
    const [selectedLibrary, setSelectedLibrary] = useState<Library | null>(null);
    const [retentionDays, setRetentionDays] = useState(90);
    const [minVersions, setMinVersions] = useState(3);
    const [cleanupInProgress, setCleanupInProgress] = useState(false);

    useEffect(() => {
        fetchVersionData();
    }, []);

    const fetchVersionData = async () => {
        try {
            setLoading(true);
            // Fetch libraries with high version counts
            const sitesRes = await api.get('/v1/sites?limit=100');
            const sites = sitesRes.data.sites || [];

            // Mock libraries data (in production, iterate through sites)
            const mockLibraries: Library[] = sites.slice(0, 10).map((site: any, index: number) => ({
                id: site.id,
                name: `Documents`,
                site_name: site.name,
                total_versions: 1000 + index * 500,
                storage_mb: 500 + index * 200,
                potential_savings_mb: 100 + index * 50,
            }));

            setLibraries(mockLibraries);
        } catch (error) {
            console.error('Failed to fetch version data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartCleanup = (library: Library) => {
        setSelectedLibrary(library);
        setCleanupDialogOpen(true);
        setActiveStep(0);
    };

    const handleNext = () => {
        setActiveStep((prev) => prev + 1);
    };

    const handleBack = () => {
        setActiveStep((prev) => prev - 1);
    };

    const handleExecuteCleanup = async () => {
        if (!selectedLibrary) return;

        try {
            setCleanupInProgress(true);
            await api.post(`/v2/storage/libraries/${selectedLibrary.id}/cleanup-versions`, {
                retention_days: retentionDays,
                min_versions_to_keep: minVersions,
            });

            setCleanupDialogOpen(false);
            setActiveStep(0);
            // Refresh data
            await fetchVersionData();
        } catch (error) {
            console.error('Cleanup failed:', error);
        } finally {
            setCleanupInProgress(false);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {/* Page Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
                        Version Control Management
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Manage document library versions and optimize storage
                    </Typography>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Summary Cards */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={2}>
                            <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="h6">Total Versions</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="primary">
                            {libraries.reduce((sum, lib) => sum + lib.total_versions, 0).toLocaleString()}
                        </Typography>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={2}>
                            <DeleteSweepIcon sx={{ mr: 1, color: 'warning.main' }} />
                            <Typography variant="h6">Storage Used</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="warning.main">
                            {libraries.reduce((sum, lib) => sum + lib.storage_mb, 0).toFixed(0)} MB
                        </Typography>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3 }}>
                        <Box display="flex" alignItems="center" mb={2}>
                            <RecommendIcon sx={{ mr: 1, color: 'success.main' }} />
                            <Typography variant="h6">Potential Savings</Typography>
                        </Box>
                        <Typography variant="h4" fontWeight={700} color="success.main">
                            {libraries.reduce((sum, lib) => sum + lib.potential_savings_mb, 0).toFixed(0)} MB
                        </Typography>
                    </Paper>
                </Grid>

                {/* Libraries Table */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Document Libraries
                        </Typography>
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Site</TableCell>
                                        <TableCell>Library</TableCell>
                                        <TableCell align="right">Total Versions</TableCell>
                                        <TableCell align="right">Storage (MB)</TableCell>
                                        <TableCell align="right">Potential Savings</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell align="center">Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {libraries.map((library) => (
                                        <TableRow key={library.id}>
                                            <TableCell>{library.site_name}</TableCell>
                                            <TableCell>{library.name}</TableCell>
                                            <TableCell align="right">
                                                {library.total_versions.toLocaleString()}
                                            </TableCell>
                                            <TableCell align="right">{library.storage_mb.toFixed(0)}</TableCell>
                                            <TableCell align="right">
                                                <Typography color="success.main" fontWeight={600}>
                                                    {library.potential_savings_mb.toFixed(0)} MB
                                                </Typography>
                                            </TableCell>
                                            <TableCell>
                                                {library.total_versions > 2000 ? (
                                                    <Chip label="High" color="error" size="small" />
                                                ) : library.total_versions > 1000 ? (
                                                    <Chip label="Medium" color="warning" size="small" />
                                                ) : (
                                                    <Chip label="Normal" color="success" size="small" />
                                                )}
                                            </TableCell>
                                            <TableCell align="center">
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    startIcon={<DeleteSweepIcon />}
                                                    onClick={() => handleStartCleanup(library)}
                                                >
                                                    Cleanup
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                </Grid>
            </Grid>

            {/* Cleanup Wizard Dialog */}
            <Dialog
                open={cleanupDialogOpen}
                onClose={() => setCleanupDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Version Cleanup Wizard</DialogTitle>
                <DialogContent>
                    <Stepper activeStep={activeStep} sx={{ my: 3 }}>
                        {CLEANUP_STEPS.map((label) => (
                            <Step key={label}>
                                <StepLabel>{label}</StepLabel>
                            </Step>
                        ))}
                    </Stepper>

                    {/* Step 1: Select Libraries */}
                    {activeStep === 0 && (
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Selected Library
                            </Typography>
                            {selectedLibrary && (
                                <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                                    <Typography><strong>Site:</strong> {selectedLibrary.site_name}</Typography>
                                    <Typography><strong>Library:</strong> {selectedLibrary.name}</Typography>
                                    <Typography>
                                        <strong>Versions:</strong> {selectedLibrary.total_versions.toLocaleString()}
                                    </Typography>
                                </Paper>
                            )}
                        </Box>
                    )}

                    {/* Step 2: Configure Settings */}
                    {activeStep === 1 && (
                        <Box>
                            <Alert severity="info" sx={{ mb: 3 }}>
                                Configure cleanup parameters. Versions older than the retention period will be
                                deleted, keeping at least the minimum versions specified.
                            </Alert>
                            <TextField
                                fullWidth
                                label="Retention Days"
                                type="number"
                                value={retentionDays}
                                onChange={(e) => setRetentionDays(Number(e.target.value))}
                                helperText="Delete versions older than this many days"
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                fullWidth
                                label="Minimum Versions to Keep"
                                type="number"
                                value={minVersions}
                                onChange={(e) => setMinVersions(Number(e.target.value))}
                                helperText="Always keep at least this many versions"
                            />
                        </Box>
                    )}

                    {/* Step 3: Review & Execute */}
                    {activeStep === 2 && (
                        <Box>
                            <Alert severity="warning" sx={{ mb: 2 }}>
                                <strong>Warning:</strong> This action will permanently delete old versions.
                                Please review carefully before proceeding.
                            </Alert>
                            <Typography variant="h6" gutterBottom>
                                Cleanup Summary
                            </Typography>
                            <Paper variant="outlined" sx={{ p: 2 }}>
                                <Typography><strong>Site:</strong> {selectedLibrary?.site_name}</Typography>
                                <Typography><strong>Library:</strong> {selectedLibrary?.name}</Typography>
                                <Typography><strong>Retention:</strong> {retentionDays} days</Typography>
                                <Typography><strong>Min Versions:</strong> {minVersions}</Typography>
                                <Typography color="success.main" fontWeight={600} sx={{ mt: 2 }}>
                                    Estimated savings: {selectedLibrary?.potential_savings_mb.toFixed(0)} MB
                                </Typography>
                            </Paper>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCleanupDialogOpen(false)}>Cancel</Button>
                    {activeStep > 0 && <Button onClick={handleBack}>Back</Button>}
                    {activeStep < CLEANUP_STEPS.length - 1 ? (
                        <Button onClick={handleNext} variant="contained">
                            Next
                        </Button>
                    ) : (
                        <Button
                            onClick={handleExecuteCleanup}
                            variant="contained"
                            color="warning"
                            disabled={cleanupInProgress}
                        >
                            {cleanupInProgress ? <CircularProgress size={24} /> : 'Execute Cleanup'}
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default VersionControlDashboard;
