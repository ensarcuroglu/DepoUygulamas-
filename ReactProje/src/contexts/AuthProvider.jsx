import { useEffect, useState } from 'react';
import { loginUser as apiLogin, getCurrentUser, logoutUser as apiLogout } from '../services/api';
import AuthContext from './AuthContext';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('user');
        if (!savedUser) return null;
        try {
            return JSON.parse(savedUser);
        } catch {
            localStorage.removeItem('user');
            return null;
        }
    });
    const [loading, setLoading] = useState(() => {
        const token = localStorage.getItem('access_token');
        const savedUser = localStorage.getItem('user');
        return Boolean(token && savedUser);
    });

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const savedUser = localStorage.getItem('user');
        if (!(token && savedUser)) return;

        getCurrentUser()
            .then((res) => {
                const freshUser = res.data;
                setUser(freshUser);
                localStorage.setItem('user', JSON.stringify(freshUser));
            })
            .catch(() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                setUser(null);
            })
            .finally(() => setLoading(false));
    }, []);

    const login = async (kullanici_adi, sifre) => {
        const res = await apiLogin({ kullanici_adi, sifre });
        const { access_token, refresh_token, user: userData } = res.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);

        return userData;
    };

    const logout = async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            try {
                await apiLogout({ refresh_token: refreshToken });
            } catch {
                // Local cleanup still runs when API logout fails.
            }
        }

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

export default AuthProvider;
