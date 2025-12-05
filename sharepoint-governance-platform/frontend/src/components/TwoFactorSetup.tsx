import { useState } from 'react'
import {
    Box,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Typography,
    Stepper,
    Step,
    StepLabel,
    Alert,
    Paper,
    List,
    ListItem,
    ListItemText,
    IconButton,
    CircularProgress,
} from '@mui/material'
import {
    QrCode2,
    ContentCopy,
    CheckCircle,
    Download,
    Delete
} from '@mui/icons-material'
import { QRCodeSVG } from 'qrcode.react'

interface TwoFactorSetupProps {
    open: boolean
    onClose: () => void
    onComplete: () => void
}

interface SetupData {
    totp_secret?: string
    qr_code_url?: string
    backup_codes?: string[]
}

interface TrustedDevice {
    device_id: string
    device_name: string
    ip_address?: string
    created_at: string
    last_used_at: string
    expires_at: string
}

const steps = ['Enable 2FA', 'Scan QR Code', 'Verify Code', 'Save Backup Codes']

export default function TwoFactorSetup({ open, onClose, onComplete }: TwoFactorSetupProps) {
    const [activeStep, setActiveStep] = useState(0)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [setupData, setSetupData] = useState<SetupData>({})
    const [verificationCode, setVerificationCode] = useState('')
    const [showManualEntry, setShowManualEntry] = useState(false)

    const handleEnable2FA = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch('/api/v1/2fa/enable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({ password: '' }), // Password validation handled by backend
            })

            if (!response.ok) {
                throw new Error('Failed to enable 2FA')
            }

            const data = await response.json()
            setSetupData(data)
            setActiveStep(1)
        } catch (err: any) {
            setError(err.message || 'Failed to enable 2FA')
        } finally {
            setLoading(false)
        }
    }

    const handleVerifyCode = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch('/api/v1/2fa/verify-setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({ totp_code: verificationCode }),
            })

            if (!response.ok) {
                throw new Error('Invalid verification code')
            }

            setActiveStep(3)
        } catch (err: any) {
            setError(err.message || 'Verification failed')
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadBackupCodes = () => {
        if (!setupData.backup_codes) return

        const content = `SharePoint Governance Platform - Backup Codes\n\nGenerated: ${new Date().toLocaleString()}\n\n${setupData.backup_codes.join('\n')}\n\nStore these codes in a safe place. Each code can only be used once.`

        const blob = new Blob([content], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'spg-backup-codes.txt'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
    }

    const handleCopySecret = () => {
        if (setupData.totp_secret) {
            navigator.clipboard.writeText(setupData.totp_secret)
        }
    }

    const handleComplete = () => {
        onComplete()
        onClose()
        // Reset state
        setActiveStep(0)
        setSetupData({})
        setVerificationCode('')
        setError(null)
    }

    const renderStepContent = () => {
        switch (activeStep) {
            case 0:
                return (
                    <Box>
                        <Typography variant="body1" paragraph>
                            Two-factor authentication adds an extra layer of security to your account.
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            You'll need an authenticator app like:
                        </Typography>
                        <List dense>
                            <ListItem>• Google Authenticator</ListItem>
                            <ListItem>• Microsoft Authenticator</ListItem>
                            <ListItem>• Authy</ListItem>
                        </List>
                        <Button
                            variant="contained"
                            fullWidth
                            onClick={handleEnable2FA}
                            disabled={loading}
                            sx={{ mt: 2 }}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Enable 2FA'}
                        </Button>
                    </Box>
                )

            case 1:
                return (
                    <Box>
                        <Typography variant="body1" paragraph>
                            Scan this QR code with your authenticator app:
                        </Typography>

                        <Paper elevation={0} sx={{ p: 3, textAlign: 'center', bgcolor: 'grey.50' }}>
                            {setupData.totp_secret && (
                                <QRCodeSVG
                                    value={`otpauth://totp/SharePoint Governance Platform?secret=${setupData.totp_secret}&issuer=SharePoint Governance Platform`}
                                    size={200}
                                    level="M"
                                />
                            )}
                        </Paper>

                        <Box sx={{ mt: 2 }}>
                            <Button
                                size="small"
                                startIcon={<QrCode2 />}
                                onClick={() => setShowManualEntry(!showManualEntry)}
                            >
                                {showManualEntry ? 'Hide' : 'Show'} Manual Entry Key
                            </Button>
                        </Box>

                        {showManualEntry && setupData.totp_secret && (
                            <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                                <Typography variant="caption" color="text.secondary">
                                    Manual Entry Key:
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                    <Typography
                                        variant="body2"
                                        sx={{
                                            fontFamily: 'monospace',
                                            wordBreak: 'break-all',
                                            flex: 1
                                        }}
                                    >
                                        {setupData.totp_secret}
                                    </Typography>
                                    <IconButton size="small" onClick={handleCopySecret}>
                                        <ContentCopy fontSize="small" />
                                    </IconButton>
                                </Box>
                            </Paper>
                        )}

                        <Button
                            variant="contained"
                            fullWidth
                            onClick={() => setActiveStep(2)}
                            sx={{ mt: 3 }}
                        >
                            Next: Verify Code
                        </Button>
                    </Box>
                )

            case 2:
                return (
                    <Box>
                        <Typography variant="body1" paragraph>
                            Enter the 6-digit code from your authenticator app:
                        </Typography>

                        <TextField
                            fullWidth
                            label="Verification Code"
                            value={verificationCode}
                            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            placeholder="123456"
                            inputProps={{
                                maxLength: 6,
                                style: { fontSize: '1.5rem', letterSpacing: '0.5rem', textAlign: 'center' }
                            }}
                            sx={{ mt: 2 }}
                        />

                        <Button
                            variant="contained"
                            fullWidth
                            onClick={handleVerifyCode}
                            disabled={verificationCode.length !== 6 || loading}
                            sx={{ mt: 3 }}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Verify & Enable'}
                        </Button>
                    </Box>
                )

            case 3:
                return (
                    <Box>
                        <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
                            2FA has been enabled successfully!
                        </Alert>

                        <Typography variant="body1" paragraph>
                            <strong>Save your backup codes</strong> - You can use these to access your account if you lose your authenticator device.
                        </Typography>

                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="subtitle2">Backup Codes</Typography>
                                <Button
                                    size="small"
                                    startIcon={<Download />}
                                    onClick={handleDownloadBackupCodes}
                                >
                                    Download
                                </Button>
                            </Box>
                            <Box sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                                {setupData.backup_codes?.map((code, index) => (
                                    <Box key={index} sx={{ py: 0.5 }}>
                                        {code}
                                    </Box>
                                ))}
                            </Box>
                        </Paper>

                        <Alert severity="warning" sx={{ mt: 2 }}>
                            Each backup code can only be used once. Store them securely!
                        </Alert>

                        <Button
                            variant="contained"
                            fullWidth
                            onClick={handleComplete}
                            sx={{ mt: 3 }}
                        >
                            Complete Setup
                        </Button>
                    </Box>
                )

            default:
                return null
        }
    }

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="sm"
            fullWidth
        >
            <DialogTitle>
                <Typography variant="h5">Setup Two-Factor Authentication</Typography>
            </DialogTitle>

            <DialogContent>
                <Stepper activeStep={activeStep} sx={{ mt: 2, mb: 4 }}>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                        {error}
                    </Alert>
                )}

                {renderStepContent()}
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
            </DialogActions>
        </Dialog>
    )
}

// Component for managing trusted devices
export function TrustedDevices() {
    const [devices, setDevices] = useState<TrustedDevice[]>([])
    const [loading, setLoading] = useState(true)

    const fetchDevices = async () => {
        try {
            const response = await fetch('/api/v1/2fa/devices', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })
            const data = await response.json()
            setDevices(data.devices || [])
        } catch (err) {
            console.error('Failed to fetch devices:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleRevokeDevice = async (deviceId: string) => {
        try {
            await fetch(`/api/v1/2fa/devices/${deviceId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })
            fetchDevices()
        } catch (err) {
            console.error('Failed to revoke device:', err)
        }
    }

    useState(() => {
        fetchDevices()
    })

    if (loading) {
        return <CircularProgress />
    }

    return (
        <Box>
            <Typography variant="h6" gutterBottom>
                Trusted Devices
            </Typography>

            {devices.length === 0 ? (
                <Typography color="text.secondary">
                    No trusted devices
                </Typography>
            ) : (
                <List>
                    {devices.map((device) => (
                        <ListItem
                            key={device.device_id}
                            secondaryAction={
                                <IconButton
                                    edge="end"
                                    onClick={() => handleRevokeDevice(device.device_id)}
                                >
                                    <Delete />
                                </IconButton>
                            }
                        >
                            <ListItemText
                                primary={device.device_name}
                                secondary={
                                    <>
                                        Last used: {new Date(device.last_used_at).toLocaleDateString()}
                                        {device.ip_address && ` • ${device.ip_address}`}
                                    </>
                                }
                            />
                        </ListItem>
                    ))}
                </List>
            )}
        </Box>
    )
}
