/**
 * Authentication utilities for frontend.
 */
import Cookies from 'js-cookie';

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
 * Get current authentication state.
 */
export async function getAuthState(): Promise<AuthState> {
    try {
        // Check if we have a token in query params (from OAuth redirect)
        if (typeof window !== 'undefined') {
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');
            if (token) {
                // Store token in cookie
                Cookies.set('access_token', token, { expires: 1 }); // 1 day
                // Remove token from URL
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        }

        const response = await fetch(`${API_URL}/auth/me`, {
            credentials: 'include', // Include cookies
        });

        if (!response.ok) {
            return { authenticated: false, user: null };
        }

        const data = await response.json();
        return {
            authenticated: data.authenticated,
            user: data.user,
        };
    } catch (error) {
        console.error('Error getting auth state:', error);
        return { authenticated: false, user: null };
    }
}

/**
 * Redirect to login page.
 */
export function login(redirectTo?: string) {
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '/';
    const redirect = redirectTo || currentPath;
    window.location.href = `${API_URL}/auth/login?redirect_to=${encodeURIComponent(redirect)}`;
}

/**
 * Logout user.
 */
export async function logout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });

        // Clear local cookie
        Cookies.remove('access_token');

        // Redirect to home
        window.location.href = '/';
    } catch (error) {
        console.error('Error logging out:', error);
        // Still redirect even if API call fails
        Cookies.remove('access_token');
        window.location.href = '/';
    }
}

/**
 * Get the access token from cookie.
 */
export function getAccessToken(): string | undefined {
    return Cookies.get('access_token');
}
