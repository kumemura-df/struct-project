/**
 * Authentication utilities for frontend.
 * 
 * SECURITY: All authentication tokens are managed via HttpOnly cookies
 * set by the backend. This file does NOT handle tokens directly.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
    email: string;
    name?: string;
    picture?: string;
}

export interface AuthState {
    authenticated: boolean;
    user: User | null;
}

/**
 * Get current authentication state from the API.
 * 
 * The backend validates the HttpOnly cookie and returns the auth state.
 * We never handle the token directly in JavaScript.
 */
export async function getAuthState(): Promise<AuthState> {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            method: 'GET',
            credentials: 'include', // Include HttpOnly cookies
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            // Not authenticated or error
            return { authenticated: false, user: null };
        }

        const data = await response.json();
        return {
            authenticated: data.authenticated ?? false,
            user: data.user ?? null,
        };
    } catch (error) {
        console.error('Error getting auth state:', error);
        return { authenticated: false, user: null };
    }
}

/**
 * Check if user is authenticated.
 */
export async function isAuthenticated(): Promise<boolean> {
    const state = await getAuthState();
    return state.authenticated;
}

/**
 * Redirect to login page.
 * 
 * @param redirectTo - Optional path to redirect to after login
 */
export function login(redirectTo?: string): void {
    if (typeof window === 'undefined') return;
    
    const currentPath = window.location.pathname;
    const redirect = redirectTo || currentPath;
    
    // Redirect to API login endpoint
    // The API will handle OAuth flow and set HttpOnly cookie on callback
    window.location.href = `${API_URL}/auth/login?redirect_to=${encodeURIComponent(redirect)}`;
}

/**
 * Logout user.
 * 
 * Calls the API logout endpoint which clears the HttpOnly cookie.
 */
export async function logout(): Promise<void> {
    if (typeof window === 'undefined') return;
    
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });
    } catch (error) {
        console.error('Error logging out:', error);
    }
    
    // Always redirect to home after logout attempt
    window.location.href = '/';
}

/**
 * Refresh authentication state.
 * 
 * This is a no-op since we use HttpOnly cookies.
 * The browser automatically sends cookies with each request.
 * 
 * @deprecated This function is kept for backwards compatibility but does nothing.
 */
export async function refreshAuth(): Promise<void> {
    // No-op: HttpOnly cookies are automatically handled by the browser
}

/**
 * Get the authentication status endpoint URL.
 * 
 * Useful for components that need to poll auth status.
 */
export function getAuthStatusUrl(): string {
    return `${API_URL}/auth/me`;
}
