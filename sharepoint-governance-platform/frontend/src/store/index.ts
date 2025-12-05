import { configureStore } from '@reduxjs/toolkit'
import authReducer from '../features/auth/authSlice'
import sitesReducer from '../features/sites/sitesSlice'

export const store = configureStore({
    reducer: {
        auth: authReducer,
        sites: sitesReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
