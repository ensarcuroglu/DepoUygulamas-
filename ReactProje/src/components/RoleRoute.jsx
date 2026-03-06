import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Rol Tabanlı Route Guard
 * Belirtilen rollere sahip olmayan kullanıcıları yönlendirir.
 * Depocu → /stok-hareketleri, diğerleri → /dashboard
 *
 * Kullanım:
 *   <Route element={<RoleRoute allowedRoles={['admin']} />}>
 *     <Route path="/dashboard" element={<DashboardPage />} />
 *   </Route>
 */
export default function RoleRoute({ allowedRoles = [] }) {
    const { user } = useAuth();

    if (!user || !allowedRoles.includes(user.rol)) {
        // Depocu veya Lojistik ise stok hareketlerine, değilse login'e yönlendir
        const redirectTo = (user?.rol === 'depocu' || user?.rol === 'lojistik') ? '/stok-hareketleri' : '/login';
        return <Navigate to={redirectTo} replace />;
    }

    return <Outlet />;
}
