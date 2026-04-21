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
export default function RoleRoute({ allowedRoles = [], allowedDepartments = [] }) {
    const { user } = useAuth();
    const userDepartment = (user?.departman || '').trim().toLowerCase();
    const departmentAllowed = allowedDepartments
        .map((department) => department.toLowerCase())
        .includes(userDepartment);
    const roleAllowed = !!user && allowedRoles.includes(user.rol);

    if (!user || (!roleAllowed && !departmentAllowed)) {
        // Yetkisiz erişim: rolüne göre uygun sayfaya yönlendir (login'e değil)
        const redirectTo = (user?.rol === 'depocu' || user?.rol === 'lojistik') 
            ? '/stok-hareketleri' 
            : (user?.rol === 'goruntuleyen') 
            ? '/profil-ayarlari' 
            : '/login';
        return <Navigate to={redirectTo} replace />;
    }

    return <Outlet />;
}
