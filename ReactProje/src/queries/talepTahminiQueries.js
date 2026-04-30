import { useQuery } from '@tanstack/react-query';
import { getTalepTahminUrunleri, getTalepTahmini } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useTalepTahminUrunleriQuery(params = {}) {
  return useQuery({
    queryKey: queryKeys.talepTahmini.products(params),
    queryFn: () => getTalepTahminUrunleri(params).then(responseData),
  });
}

export function useTalepTahminiQuery(urunId, tahminGun) {
  return useQuery({
    queryKey: queryKeys.talepTahmini.detail(urunId, tahminGun),
    queryFn: () => getTalepTahmini(urunId, tahminGun).then(responseData),
    enabled: Boolean(urunId),
  });
}

