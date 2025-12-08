import { useState } from 'react'
import {
    Box,
    Container,
    Paper,
    Typography,
    Button,
    Stepper,
    Step,
    StepLabel,
    TextField,
    Alert,
    CircularProgress,
    Link,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material'
import { Help, CheckCircle } from '@mui/icons-material'

const steps = [
    'Welcome',
    'Database',
    'Microsoft 365',
    'Active Directory',
    'Security',
    'Complete'
]

interface HelpDialogProps {
    open: boolean
    onClose: () => void
    title: string
    content: React.ReactNode
}

function HelpDialog({ open, onClose, title, content }: HelpDialogProps) {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent dividers>
                {content}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Close</Button>
            </DialogActions>
        </Dialog>
    )
}

export default function SetupWizard() {
    const [activeStep, setActiveStep] = useState(0)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [helpDialog, setHelpDialog] = useState<{ open: boolean; title: string; content: React.ReactNode }>({
        open: false,
        title: '',
        content: null
    })

    // Database config
    const [dbHost, setDbHost] = useState('localhost')
    const [dbPort, setDbPort] = useState('5432')
    const [dbName, setDbName] = useState('spg_db')
    const [dbUser, setDbUser] = useState('spg_user')
    const [dbPassword, setDbPassword] = useState('')

    // Azure config
    const [tenantId, setTenantId] = useState('')
    const [clientId, setClientId] = useState('')
    const [clientSecret, setClientSecret] = useState('')
    const [sharepointUrl, setSharepointUrl] = useState('')

    // LDAP config
    const [ldapServer, setLdapServer] = useState('')
    const [ldapBaseDn, setLdapBaseDn] = useState('')
    const [ldapBindDn, setLdapBindDn] = useState('')
    const [ldapBindPassword, setLdapBindPassword] = useState('')

    // Security
    const [jwtSecret, setJwtSecret] = useState('')

    const handleNext = () => {
        setActiveStep((prevStep) => prevStep + 1)
    }

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1)
    }

    const handleTestDatabase = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch('/api/v1/setup/validate-database', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    host: dbHost,
                    port: parseInt(dbPort),
                    database: dbName,
                    username: dbUser,
                    password: dbPassword,
                }),
            })

            const data = await response.json()
            if (data.valid) {
                alert('Database connection successful!')
            } else {
                setError(data.message)
            }
        } catch (err: any) {
            setError(err.message || 'Failed to test database connection')
        } finally {
            setLoading(false)
        }
    }

    const handleGenerateSecret = async () => {
        try {
            const response = await fetch('/api/v1/setup/generate-secret', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })
            const data = await response.json()
            setJwtSecret(data.secret)
        } catch (err) {
            console.error('Failed to generate secret:', err)
        }
    }

    const showAzureHelp = () => {
        setHelpDialog({
            open: true,
            title: 'Azure AD Setup Guide',
            content: (
                <Box>
                    <Typography variant="h6" gutterBottom>How to get Azure AD credentials:</Typography>
                    <ol>
                        <li>
                            <Typography paragraph>
                                Go to <Link href="https://portal.azure.com" target="_blank">Azure Portal</Link>
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Navigate to <strong>Azure Active Directory</strong> → <strong>App Registrations</strong>
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Click <strong>New registration</strong>
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Name: "SharePoint Governance Platform"
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Copy the <strong>Application (client) ID</strong> → This is your Client ID
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Copy the <strong>Directory (tenant) ID</strong> → This is your Tenant ID
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Go to <strong>Certificates & secrets</strong> → <strong>New client secret</strong>
                            </Typography>
                        </li>
                        <li>
                            <Typography paragraph>
                                Copy the secret <strong>Value</strong> immediately (you won't see it again!)
                            </Typography>
                        </li>
                    </ol>
                    <Alert severity="info">
                        For detailed instructions, see the Configuration Guide documentation.
                    </Alert>
                </Box>
            )
        })
    }

    const renderStepContent = () => {
        switch (activeStep) {
            case 0:
                return (
                    <Box>
                        <Typography variant="h5" gutterBottom>
                            Welcome to SharePoint Governance Platform
                        </Typography>
                        <Typography paragraph>
                            This wizard will guide you through the initial configuration of your platform.
                        </Typography>
                        <Typography paragraph>
                            You will need:
                        </Typography>
                        <ul>
                            <li>PostgreSQL database credentials</li>
                            <li>Azure AD app registration details</li>
                            <li>Active Directory/LDAP connection info</li>
                        </ul>
                        <Alert severity="info" sx={{ mt: 2 }}>
                            See the Configuration Guide for detailed instructions on obtaining these credentials.
                        </Alert>
                    </Box>
                )

            case 1:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Database Configuration
                        </Typography>
                        <TextField
                            fullWidth
                            label="Host"
                            value={dbHost}
                            onChange={(e) => setDbHost(e.target.value)}
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="Port"
                            value={dbPort}
                            onChange={(e) => setDbPort(e.target.value)}
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="Database Name"
                            value={dbName}
                            onChange={(e) => setDbName(e.target.value)}
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="Username"
                            value={dbUser}
                            onChange={(e) => setDbUser(e.target.value)}
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="Password"
                            type="password"
                            value={dbPassword}
                            onChange={(e) => setDbPassword(e.target.value)}
                            margin="normal"
                        />
                        <Button
                            variant="outlined"
                            onClick={handleTestDatabase}
                            disabled={loading}
                            sx={{ mt: 2 }}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Test Connection'}
                        </Button>
                    </Box>
                )

            case 2:
                return (
                    <Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="h6" gutterBottom>
                                Microsoft 365 Configuration
                            </Typography>
                            <Button startIcon={<Help />} onClick={showAzureHelp}>
                                How to get these?
                            </Button>
                        </Box>
                        <TextField
                            fullWidth
                            label="Tenant ID"
                            value={tenantId}
                            onChange={(e) => setTenantId(e.target.value)}
                            margin="normal"
                            helperText="From Azure AD → Overview"
                        />
                        <TextField
                            fullWidth
                            label="Client ID"
                            value={clientId}
                            onChange={(e) => setClientId(e.target.value)}
                            margin="normal"
                            helperText="From App Registration"
                        />
                        <TextField
                            fullWidth
                            label="Client Secret"
                            type="password"
                            value={clientSecret}
                            onChange={(e) => setClientSecret(e.target.value)}
                            margin="normal"
                            helperText="From Certificates & secrets"
                        />
                        <TextField
                            fullWidth
                            label="SharePoint Site URL"
                            value={sharepointUrl}
                            onChange={(e) => setSharepointUrl(e.target.value)}
                            margin="normal"
                            placeholder="https://yourtenant.sharepoint.com"
                        />
                    </Box>
                )

            case 3:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Active Directory / LDAP
                        </Typography>
                        <TextField
                            fullWidth
                            label="LDAP Server"
                            value={ldapServer}
                            onChange={(e) => setLdapServer(e.target.value)}
                            margin="normal"
                            placeholder="ldap://dc01.company.com:389"
                        />
                        <TextField
                            fullWidth
                            label="Base DN"
                            value={ldapBaseDn}
                            onChange={(e) => setLdapBaseDn(e.target.value)}
                            margin="normal"
                            placeholder="dc=company,dc=com"
                        />
                        <TextField
                            fullWidth
                            label="Bind DN (Service Account)"
                            value={ldapBindDn}
                            onChange={(e) => setLdapBindDn(e.target.value)}
                            margin="normal"
                            placeholder="cn=svc_spg,ou=ServiceAccounts,dc=company,dc=com"
                        />
                        <TextField
                            fullWidth
                            label="Bind Password"
                            type="password"
                            value={ldapBindPassword}
                            onChange={(e) => setLdapBindPassword(e.target.value)}
                            margin="normal"
                        />
                    </Box>
                )

            case 4:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Security Configuration
                        </Typography>
                        <Box display="flex" gap={1} alignItems="flex-end" mt={2}>
                            <TextField
                                fullWidth
                                label="JWT Secret Key"
                                value={jwtSecret}
                                onChange={(e) => setJwtSecret(e.target.value)}
                                helperText="Minimum 32 characters"
                                inputProps={{ style: { fontFamily: 'monospace' } }}
                            />
                            <Button
                                variant="outlined"
                                onClick={handleGenerateSecret}
                                sx={{ mb: 2.8 }}
                            >
                                Generate
                            </Button>
                        </Box>
                    </Box>
                )

            case 5:
                return (
                    <Box textAlign="center">
                        <CheckCircle color="success" sx={{ fontSize: 80, mb: 2 }} />
                        <Typography variant="h5" gutterBottom>
                            Setup Complete!
                        </Typography>
                        <Typography paragraph>
                            Your SharePoint Governance Platform is now configured and ready to use.
                        </Typography>
                        <Alert severity="success">
                            Configuration has been saved. You can now start using the platform.
                        </Alert>
                    </Box>
                )

            default:
                return null
        }
    }

    return (
        <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
            <Paper sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Setup Wizard
                </Typography>

                <Stepper activeStep={activeStep} sx={{ my: 4 }}>
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

                <Box sx={{ minHeight: 400 }}>
                    {renderStepContent()}
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                    <Button
                        disabled={activeStep === 0}
                        onClick={handleBack}
                    >
                        Back
                    </Button>
                    <Button
                        variant="contained"
                        onClick={handleNext}
                        disabled={activeStep === steps.length - 1}
                    >
                        {activeStep === steps.length - 2 ? 'Complete Setup' : 'Next'}
                    </Button>
                </Box>
            </Paper>

            <HelpDialog
                open={helpDialog.open}
                onClose={() => setHelpDialog({ ...helpDialog, open: false })}
                title={helpDialog.title}
                content={helpDialog.content}
            />
        </Container>
    )
}
