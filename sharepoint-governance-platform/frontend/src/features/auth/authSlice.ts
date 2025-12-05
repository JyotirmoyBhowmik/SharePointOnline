import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import api from '../../services/api'

interface User {
    email: string
    name: string
    role: string
    department?: string
}

interface AuthState {
    user: User | null
    token: string | null
    refreshToken: string | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null
}

const initialState: AuthState = {
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refreshToken'),
    isAuthenticated: !!localStorage.getItem('token'),
    isLoading: false,
    error: null,
}

export const login = createAsyncThunk(
    'auth/login',
    async (credentials: { username: string; password: string }) => {
        const response = await api.post('/auth/login', credentials)
        return response.data
    }
)

export const logout = createAsyncThunk('auth/logout', async () => {
    await api.post('/auth/logout')
})

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null
        },
    },
    extraReducers: (builder) => {
        builder
            // Login
            .addCase(login.pending, (state) => {
                state.isLoading = true
                state.error = null
            })
            .addCase(login.fulfilled, (state, action: PayloadAction<any>) => {
                state.isLoading = false
                state.isAuthenticated = true
                state.user = action.payload.user
                state.token = action.payload.access_token
                state.refreshToken = action.payload.refresh_token

                // Store in localStorage
                localStorage.setItem('user', JSON.stringify(action.payload.user))
                localStorage.setItem('token', action.payload.access_token)
                localStorage.setItem('refreshToken', action.payload.refresh_token)
            })
            .addCase(login.rejected, (state, action) => {
                state.isLoading = false
                state.error = action.error.message || 'Login failed'
            })

            // Logout
            .addCase(logout.fulfilled, (state) => {
                state.user = null
                state.token = null
                state.refreshToken = null
                state.isAuthenticated = false

                // Clear localStorage
                localStorage.removeItem('user')
                localStorage.removeItem('token')
                localStorage.removeItem('refreshToken')
            })
    },
})

export const { clearError } = authSlice.actions
export default authSlice.reducer
