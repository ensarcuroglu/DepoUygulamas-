import { useQuery } from '@tanstack/react-query';
import { operatorPerformansApi } from '../services/operatorPerformansApi';
import { queryKeys } from './queryKeys';

const ONBES_DK = 15 * 60 * 1000;

export function useOperatorOzetQuery(params = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.operatorPerformans.ozet(params),
    queryFn: () => operatorPerformansApi.ozet(params),
    staleTime: ONBES_DK,
    ...options,
  });
}

export function useLeaderboardQuery(params = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.operatorPerformans.leaderboard(params),
    queryFn: () => operatorPerformansApi.leaderboard(params),
    staleTime: 60 * 1000,
    ...options,
  });
}

export function useKendiPerformansimQuery(params = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.operatorPerformans.benim(params),
    queryFn: () => operatorPerformansApi.benimMetriklerim(params),
    staleTime: 60 * 1000,
    refetchOnWindowFocus: true,
    ...options,
  });
}

export function useKullaniciPerformansDetayQuery(kullaniciId, params = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.operatorPerformans.kullanici(kullaniciId, params),
    queryFn: () => operatorPerformansApi.kullaniciDetay(kullaniciId, params),
    enabled: Boolean(kullaniciId),
    staleTime: ONBES_DK,
    ...options,
  });
}
