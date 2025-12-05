import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { RootState } from './store'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Sites from './pages/Sites'
import AccessReviews from './pages/AccessReviews'
import Layout from './components/Layout'

function App() {
    const { isAuthenticated } = useSelector((state: RootState) => state.auth)

    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            {/* Protected routes */}
            <Route
                path="/"
                element={isAuthenticated ? <Layout /> : <Navigate to="/login" replace />}
            >
                <Route index element={<Dashboard />} />
                <Route path="sites" element={<Sites />} />
                <Route path="access-reviews" element={<AccessReviews />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
