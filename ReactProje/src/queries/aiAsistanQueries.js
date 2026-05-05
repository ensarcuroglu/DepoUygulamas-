import { useMutation, useQuery } from '@tanstack/react-query';
import { aiSorgula, aiOturumSifirla, getAiSema } from '../services/aiAsistanApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useAiSorgulaMutation() {
  return useMutation({
    mutationFn: (payload) => aiSorgula(payload).then(responseData),
  });
}

export function useAiOturumSifirlaMutation() {
  return useMutation({
    mutationFn: (sessionId) => aiOturumSifirla(sessionId).then(responseData),
  });
}

export function useAiSemaQuery({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.aiAsistan.sema(),
    queryFn: () => getAiSema().then(responseData),
    staleTime: 1000 * 60 * 60,
    enabled,
  });
}
