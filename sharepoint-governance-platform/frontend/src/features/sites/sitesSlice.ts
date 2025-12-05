import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../../services/api'

interface Site {
    site_id: string
    name: string
    site_url: string
    classification: string
    storage_used_mb: number
    last_activity: string
    is_archived: boolean
}

interface SitesState {
    items: Site[]
    total: number
    isLoading: boolean
    error: string | null
}

const initialState: SitesState = {
    items: [],
    total: 0,
    isLoading: false,
    error: null,
}

export const fetchSites = createAsyncThunk(
    'sites/fetchSites',
    async (params: { skip?: number; limit?: number; search?: string } = {}) => {
        const response = await api.get('/sites', { params })
        return response.data
    }
)

const sitesSlice = createSlice({
    name: 'sites',
    initialState,
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchSites.pending, (state) => {
                state.isLoading = true
                state.error = null
            })
            .addCase(fetchSites.fulfilled, (state, action) => {
                state.isLoading = false
                state.items = action.payload.sites
                state.total = action.payload.total
            })
            .addCase(fetchSites.rejected, (state, action) => {
                state.isLoading = false
                state.error = action.error.message || 'Failed to fetch sites'
            })
    },
})

export default sitesSlice.reducer
