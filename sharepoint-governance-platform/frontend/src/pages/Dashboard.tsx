import { Typography } from '@mui/material'

export default function Dashboard(): JSX.Element {
    return (
        <div>
            <Typography variant="h4" gutterBottom>
                Dashboard
            </Typography>
            <Typography variant="body1">
                Welcome to the SharePoint Governance Platform. Select a section from the navigation to get started.
            </Typography>
        </div>
    )
}
