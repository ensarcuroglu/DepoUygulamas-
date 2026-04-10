import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Korumalı Route Wrapper
 * Giriş yapmamış kullanıcıları /login sayfasına yönlendirir.
 * Kullanım: <Route element={<PrivateRoute />}> ... </Route>
 */
export default function PrivateRoute() {
    const { user, loading } = useAuth();

    // Token doğrulanırken loading ekranı göster
    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-[3px] border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                    <p className="text-sm font-medium text-slate-500">Oturum doğrulanıyor...</p>
                </div>
            </div>
        );
    }

    return user ? <Outlet /> : <Navigate to="/login" replace />;
}
