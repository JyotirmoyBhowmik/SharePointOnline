import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
    Box,
    Container,
    Paper,
    TextField,
    Button,
    Typography,
    Alert,
    CircularProgress,
    Checkbox,
    FormControlLabel,
    Link,
} from '@mui/material'
import { login, clearError } from '../features/auth/authSlice'
import { RootState, AppDispatch } from '../store'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [twoFactorCode, setTwoFactorCode] = useState('')
    const [backupCode, setBackupCode] = useState('')
    const [trustDevice, setTrustDevice] = useState(false)
    const [showBackupCode, setShowBackupCode] = useState(false)
    const [requires2FA, setRequires2FA] = useState(false)
    const [intermediateToken, setIntermediateToken] = useState<string | null>(null)
    const [customError, setCustomError] = useState<string | null>(null)

    const dispatch = useDispatch<AppDispatch>()
    const navigate = useNavigate()
    const { isLoading, error } = useSelector((state: RootState) => state.auth)

    const displayError = customError || error

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        dispatch(clearError())
        setCustomError(null)

        const result = await dispatch(login({ username, password }))
        if (login.fulfilled.match(result)) {
            const response = result.payload as any

            // Check if 2FA is required
            if (response.requires_2fa) {
                setRequires2FA(true)
                setIntermediateToken(response.intermediate_token || response.access_token)
            } else {
                // No 2FA required, navigate to dashboard
                navigate('/')
            }
        }
    }

    const handleVerify2FA = async (e: React.FormEvent) => {
        e.preventDefault()
        setCustomError(null)

        try {
            const response = await fetch('/api/v1/2fa/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${intermediateToken}`,
                },
                body: JSON.stringify({
                    totp_code: showBackupCode ? undefined : twoFactorCode,
                    backup_code: showBackupCode ? backupCode : undefined,
                    trust_device: trustDevice,
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Invalid verification code')
            }

            const data = await response.json()

            // Store the full access token
            localStorage.setItem('token', data.access_token)
            if (data.refresh_token) {
                localStorage.setItem('refreshToken', data.refresh_token)
            }

            // Navigate to dashboard
            navigate('/')
        } catch (err: any) {
            setCustomError(err.message || 'Verification failed')
        }
    }

    if (requires2FA) {
        return (
            <Container maxWidth="sm">
                <Box
                    sx={{
                        marginTop: 8,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                    }}
                >
                    <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
                        <Typography component="h1" variant="h4" align="center" gutterBottom>
                            Two-Factor Authentication
                        </Typography>
                        <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
                            {showBackupCode
                                ? 'Enter one of your backup codes'
                                : 'Enter the 6-digit code from your authenticator app'
                            }
                        </Typography>

                        {displayError && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                                {displayError}
                            </Alert>
                        )}

                        <Box component="form" onSubmit={handleVerify2FA}>
                            {!showBackupCode ? (
                                <TextField
                                    margin="normal"
                                    required
                                    fullWidth
                                    label="Verification Code"
                                    value={twoFactorCode}
                                    onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                    placeholder="123456"
                                    autoFocus
                                    inputProps={{
                                        maxLength: 6,
                                        style: { fontSize: '1.5rem', letterSpacing: '0.5rem', textAlign: 'center' }
                                    }}
                                />
                            ) : (
                                <TextField
                                    margin="normal"
                                    required
                                    fullWidth
                                    label="Backup Code"
                                    value={backupCode}
                                    onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                                    placeholder="XXXXXXXX"
                                    autoFocus
                                    inputProps={{
                                        style: { fontFamily: 'monospace', textAlign: 'center' }
                                    }}
                                />
                            )}

                            <FormControlLabel
                                control={
                                    <Checkbox
                                        checked={trustDevice}
                                        onChange={(e) => setTrustDevice(e.target.checked)}
                                        color="primary"
                                    />
                                }
                                label="Trust this device for 30 days"
                                sx={{ mt: 1 }}
                            />

                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2 }}
                                disabled={isLoading || (!showBackupCode && twoFactorCode.length !== 6) || (showBackupCode && !backupCode)}
                            >
                                {isLoading ? <CircularProgress size={24} /> : 'Verify'}
                            </Button>

                            <Box sx={{ textAlign: 'center' }}>
                                <Link
                                    component="button"
                                    type="button"
                                    variant="body2"
                                    onClick={() => {
                                        setShowBackupCode(!showBackupCode)
                                        setTwoFactorCode('')
                                        setBackupCode('')
                                        setCustomError(null)
                                    }}
                                    sx={{ cursor: 'pointer' }}
                                >
                                    {showBackupCode ? 'Use authenticator code' : 'Use backup code'}
                                </Link>
                            </Box>
                        </Box>
                    </Paper>
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="sm">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}
            >
                <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
                    <Typography component="h1" variant="h4" align="center" gutterBottom>
                        SharePoint Governance Platform
                    </Typography>
                    <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
                        Sign in with your Active Directory credentials
                    </Typography>

                    {displayError && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {displayError}
                        </Alert>
                    )}

                    <Box component="form" onSubmit={handleSubmit}>
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            id="username"
                            label="Username or Email"
                            name="username"
                            autoComplete="username"
                            autoFocus
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={isLoading}
                        />
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            name="password"
                            label="Password"
                            type="password"
                            id="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                        />
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            sx={{ mt: 3, mb: 2 }}
                            disabled={isLoading}
                        >
                            {isLoading ? <CircularProgress size={24} /> : 'Sign In'}
                        </Button>
                    </Box>
                </Paper>
            </Box>
        </Container>
    )
}
