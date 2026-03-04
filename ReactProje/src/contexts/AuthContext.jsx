import { createContext, useContext, useState, useEffect } from 'react';
import { loginUser as apiLogin, getCurrentUser } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Uygulama ilk yüklendiğinde token'ı kontrol et
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const savedUser = localStorage.getItem('user');

        if (token && savedUser) {
            // Kaydedilmiş kullanıcıyı hemen göster
            setUser(JSON.parse(savedUser));

            // Arka planda token geçerliliğini doğrula
            getCurrentUser()
                .then((res) => {
                    const freshUser = res.data;
                    setUser(freshUser);
                    localStorage.setItem('user', JSON.stringify(freshUser));
                })
                .catch(() => {
                    // Token geçersiz — oturumu temizle
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('user');
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (kullanici_adi, sifre) => {
        const res = await apiLogin({ kullanici_adi, sifre });
        const { access_token, user: userData } = res.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);

        return userData;
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
