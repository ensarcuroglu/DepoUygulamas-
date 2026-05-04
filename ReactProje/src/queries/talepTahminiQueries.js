import { useQuery } from '@tanstack/react-query';
import {
  getBacktestOzet,
  getRiskliUrunler,
  getTalepTahminUrunleri,
  getTalepTahmini,
} from '../services/api';
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

export function useRiskliUrunlerQuery(params = {}) {
  return useQuery({
    queryKey: queryKeys.talepTahmini.riskli(params),
    queryFn: () => getRiskliUrunler(params).then(responseData),
    staleTime: 5 * 60 * 1000,
  });
}

export function useBacktestOzetQuery(tahminGun = 7) {
  return useQuery({
    queryKey: queryKeys.talepTahmini.backtest(tahminGun),
    queryFn: () => getBacktestOzet(tahminGun).then(responseData),
    staleTime: 60 * 60 * 1000,
  });
}

