import { useState, useEffect } from 'react'
import {
    Box,
    Container,
    Paper,
    Typography,
    Button,
    Switch,
    FormControlLabel,
    Alert,
    Divider,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
} from '@mui/material'
import { Security, Shield, Devices } from '@mui/icons-material'
import TwoFactorSetup, { TrustedDevices } from '../components/TwoFactorSetup'

interface TwoFactorStatus {
    enabled: boolean
    setup_started: boolean
    enabled_at?: string
    last_used_at?: string
    backup_codes_remaining?: number
}

export default function SecuritySettings() {
    const [twoFactorStatus, setTwoFactorStatus] = useState<TwoFactorStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [showSetup, setShowSetup] = useState(false)
    const [showDisableDialog, setShowDisableDialog] = useState(false)
    const [disableCode, setDisableCode] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    const fetch2FAStatus = async () => {
        try {
            const response = await fetch('/api/v1/2fa/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })
            const data = await response.json()
            setTwoFactorStatus(data)
        } catch (err) {
            console.error('Failed to fetch 2FA status:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetch2FAStatus()
    }, [])

    const handleEnable2FA = () => {
        setShowSetup(true)
    }

    const handleDisable2FA = async () => {
        setError(null)

        try {
            const response = await fetch('/api/v1/2fa/disable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    password: '',
                    totp_code: disableCode,
                }),
            })

            if (!response.ok) {
                throw new Error('Failed to disable 2FA')
            }

            setSuccess('Two-factor authentication has been disabled')
            setShowDisableDialog(false)
            setDisableCode('')
            fetch2FAStatus()
        } catch (err: any) {
            setError(err.message || 'Failed to disable 2FA')
        }
    }

    const handleSetupComplete = () => {
        setSuccess('Two-factor authentication has been enabled successfully!')
        setShowSetup(false)
        fetch2FAStatus()
    }

    const handleRegenerateBackupCodes = async () => {
        try {
            const response = await fetch('/api/v1/2fa/backup-codes/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })

            if (!response.ok) {
                throw new Error('Failed to regenerate backup codes')
            }

            const data = await response.json()

            // Download the new backup codes
            const content = `SharePoint Governance Platform - Backup Codes\n\nGenerated: ${new Date().toLocaleString()}\n\n${data.backup_codes.join('\n')}\n\nStore these codes in a safe place. Each code can only be used once.`
            const blob = new Blob([content], { type: 'text/plain' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'spg-backup-codes-new.txt'
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)

            setSuccess('New backup codes generated and downloaded')
            fetch2FAStatus()
        } catch (err: any) {
            setError(err.message || 'Failed to regenerate backup codes')
        }
    }

    if (loading) {
        return (
            <Container maxWidth="md" sx={{ mt: 4 }}>
                <Box display="flex" justifyContent="center" mt={4}>
                    <CircularProgress />
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Typography variant="h4" gutterBottom>
                <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
                Security Settings
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
                    {success}
                </Alert>
            )}

            {/* Two-Factor Authentication Section */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            <Shield sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Two-Factor Authentication
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Add an extra layer of security to your account
                        </Typography>
                    </Box>

                    <FormControlLabel
                        control={
                            <Switch
                                checked={twoFactorStatus?.enabled || false}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        handleEnable2FA()
                                    } else {
                                        setShowDisableDialog(true)
                                    }
                                }}
                                color="primary"
                            />
                        }
                        label={twoFactorStatus?.enabled ? 'Enabled' : 'Disabled'}
                    />
                </Box>

                {twoFactorStatus?.enabled && (
                    <>
                        <Divider sx={{ my: 2 }} />

                        <Box>
                            <Typography variant="body2" gutterBottom>
                                <strong>Status:</strong> Active
                            </Typography>
                            {twoFactorStatus.enabled_at && (
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Enabled on: {new Date(twoFactorStatus.enabled_at).toLocaleDateString()}
                                </Typography>
                            )}
                            {twoFactorStatus.last_used_at && (
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Last used: {new Date(twoFactorStatus.last_used_at).toLocaleString()}
                                </Typography>
                            )}

                            <Box mt={2}>
                                <Typography variant="body2" gutterBottom>
                                    Backup Codes Remaining: {twoFactorStatus.backup_codes_remaining || 0} / 10
                                </Typography>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={handleRegenerateBackupCodes}
                                    sx={{ mt: 1 }}
                                >
                                    Regenerate Backup Codes
                                </Button>
                            </Box>
                        </Box>
                    </>
                )}
            </Paper>

            {/* Trusted Devices Section */}
            {twoFactorStatus?.enabled && (
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        <Devices sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Trusted Devices
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Devices that don't require 2FA for 30 days
                    </Typography>

                    <Divider sx={{ my: 2 }} />

                    <TrustedDevices />
                </Paper>
            )}

            {/* 2FA Setup Dialog */}
            <TwoFactorSetup
                open={showSetup}
                onClose={() => setShowSetup(false)}
                onComplete={handleSetupComplete}
            />

            {/* Disable 2FA Confirmation Dialog */}
            <Dialog open={showDisableDialog} onClose={() => setShowDisableDialog(false)}>
                <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" paragraph>
                        Are you sure you want to disable 2FA? This will make your account less secure.
                    </Typography>
                    <Typography variant="body2" paragraph>
                        Enter your current 2FA code to confirm:
                    </Typography>
                    <TextField
                        fullWidth
                        label="Verification Code"
                        value={disableCode}
                        onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="123456"
                        inputProps={{
                            maxLength: 6,
                            style: { fontSize: '1.2rem', letterSpacing: '0.3rem', textAlign: 'center' }
                        }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => {
                        setShowDisableDialog(false)
                        setDisableCode('')
                    }}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleDisable2FA}
                        color="error"
                        variant="contained"
                        disabled={disableCode.length !== 6}
                    >
                        Disable 2FA
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    )
}
