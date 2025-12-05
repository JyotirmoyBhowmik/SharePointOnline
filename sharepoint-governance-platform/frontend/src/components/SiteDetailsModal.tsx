/**
 * Site Details Modal with Drill-Down Navigation
 * ==============================================
 * 
 * Author: Jyotirmoy Bhowmik
 * Version: 3.0.0
 * 
 * Description:
 *   Modal component for displaying detailed site information with drill-down capabilities.
 *   Includes tabs for Overview, Access Matrix, Reviews, and Audit History.
 */

import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    IconButton,
    Tabs,
    Tab,
    Box,
    Typography,
    CircularProgress,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Breadcrumbs,
    Link,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import api from '../services/api';

interface SiteDetailsModalProps {
    open: boolean;
    onClose: () => void;
    siteId: string;
    siteName: string;
}

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
    return (
        <div role="tabpanel" hidden={value !== index}>
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
        </div>
    );
};

const SiteDetailsModal: React.FC<SiteDetailsModalProps> = ({
    open,
    onClose,
    siteId,
    siteName,
}) => {
    const [currentTab, setCurrentTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [siteDetails, setSiteDetails] = useState<any>(null);
    const [accessMatrix, setAccessMatrix] = useState<any[]>([]);
    const [breadcrumbPath, setBreadcrumbPath] = useState<string[]>(['Sites', siteName]);

    // Fetch site details
    useEffect(() => {
        if (open && siteId) {
            fetchSiteDetails();
        }
    }, [open, siteId]);

    const fetchSiteDetails = async () => {
        setLoading(true);
        try {
            const [detailsRes, accessRes] = await Promise.all([
                api.get(`/v1/sites/${siteId}`),
                api.get(`/v1/sites/${siteId}/access`),
            ]);
            setSiteDetails(detailsRes.data);
            setAccessMatrix(accessRes.data.access_matrix || []);
        } catch (error) {
            console.error('Failed to fetch site details:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setCurrentTab(newValue);
        // Update breadcrumb based on tab
        const tabNames = ['Overview', 'Access Matrix', 'Reviews', 'Audit History'];
        setBreadcrumbPath(['Sites', siteName, tabNames[newValue]]);
    };

    const handleBreadcrumbClick = (index: number) => {
        if (index === 0) {
            onClose(); // Return to sites list
        } else if (index === 1) {
            setCurrentTab(0); // Return to overview
            setBreadcrumbPath(['Sites', siteName]);
        }
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="lg"
            fullWidth
            PaperProps={{
                sx: { height: '90vh' },
            }}
        >
            {/* Header with breadcrumbs */}
            <DialogTitle>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />}>
                            {breadcrumbPath.map((path, index) => (
                                <Link
                                    key={index}
                                    component="button"
                                    variant="body1"
                                    onClick={() => handleBreadcrumbClick(index)}
                                    sx={{
                                        cursor: 'pointer',
                                        textDecoration: index === breadcrumbPath.length - 1 ? 'none' : 'underline',
                                        color: index === breadcrumbPath.length - 1 ? 'text.primary' : 'primary.main',
                                        fontWeight: index === breadcrumbPath.length - 1 ? 600 : 400,
                                    }}
                                >
                                    {path}
                                </Link>
                            ))}
                        </Breadcrumbs>
                    </Box>
                    <IconButton onClick={onClose} size="small">
                        <CloseIcon />
                    </IconButton>
                </Box>
            </DialogTitle>

            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={currentTab} onChange={handleTabChange}>
                    <Tab label="Overview" />
                    <Tab label="Access Matrix" />
                    <Tab label="Reviews" />
                    <Tab label="Audit History" />
                </Tabs>
            </Box>

            {/* Tab Content */}
            <DialogContent>
                {loading ? (
                    <Box display="flex" justifyContent="center" p={4}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <>
                        {/* Overview Tab */}
                        <TabPanel value={currentTab} index={0}>
                            {siteDetails && (
                                <Box>
                                    <Typography variant="h6" gutterBottom>
                                        Site Information
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>URL:</strong> {siteDetails.site_url}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Classification:</strong>{' '}
                                            <Chip
                                                label={siteDetails.classification}
                                                size="small"
                                                color="primary"
                                            />
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Storage:</strong> {siteDetails.storage_used_mb} MB /{' '}
                                            {siteDetails.storage_quota_mb} MB
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Last Activity:</strong>{' '}
                                            {siteDetails.last_activity
                                                ? new Date(siteDetails.last_activity).toLocaleDateString()
                                                : 'N/A'}
                                        </Typography>
                                    </Box>
                                </Box>
                            )}
                        </TabPanel>

                        {/* Access Matrix Tab */}
                        <TabPanel value={currentTab} index={1}>
                            <TableContainer component={Paper} variant="outlined">
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>User/Group</TableCell>
                                            <TableCell>Permission Level</TableCell>
                                            <TableCell>Type</TableCell>
                                            <TableCell>External</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {accessMatrix.map((access, index) => (
                                            <TableRow key={index}>
                                                <TableCell>{access.principal_name}</TableCell>
                                                <TableCell>
                                                    <Chip label={access.permission_level} size="small" />
                                                </TableCell>
                                                <TableCell>{access.principal_type}</TableCell>
                                                <TableCell>
                                                    {access.is_external_user && (
                                                        <Chip label="External" size="small" color="warning" />
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </TabPanel>

                        {/* Reviews Tab */}
                        <TabPanel value={currentTab} index={2}>
                            <Typography variant="body1" color="text.secondary">
                                Access review history will be displayed here
                            </Typography>
                        </TabPanel>

                        {/* Audit History Tab */}
                        <TabPanel value={currentTab} index={3}>
                            <Typography variant="body1" color="text.secondary">
                                Audit trail for this site will be displayed here
                            </Typography>
                        </TabPanel>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
};

export default SiteDetailsModal;
