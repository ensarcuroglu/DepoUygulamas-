import { useQuery } from '@tanstack/react-query';
import { getDashboardStats, getKritikUrunler, getStokHareketleri } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useDashboardStatsQuery() {
    return useQuery({
        queryKey: queryKeys.dashboard.stats(),
        queryFn: () => getDashboardStats().then(responseData),
    });
}

export function useKritikUrunlerQuery() {
    return useQuery({
        queryKey: queryKeys.urunler.critical(),
        queryFn: () => getKritikUrunler().then(responseData),
    });
}

export function useRecentStokHareketleriQuery(params = { limit: 4 }) {
    return useQuery({
        queryKey: queryKeys.dashboard.recentMovements(params),
        queryFn: () => getStokHareketleri(params).then(responseData),
    });
}
