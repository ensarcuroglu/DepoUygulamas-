import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createDepo, createRaf, getDepolar, getRaflar, getRafOneri } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useDepolarQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.depolar.list(params),
        queryFn: () => getDepolar(params).then(responseData),
        ...options,
    });
}

export function useRaflarQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.raflar.list(params),
        queryFn: () => getRaflar(params).then(responseData),
        ...options,
    });
}

export function useCreateDepoMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createDepo,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.depolar.all });
            queryClient.invalidateQueries({ queryKey: queryKeys.kullanicilar.all });
        },
    });
}

export function useRafOneriQuery(paletId, options = {}) {
    return useQuery({
        queryKey: queryKeys.yerlestirme.oneri(paletId),
        queryFn: () => getRafOneri(paletId).then(responseData),
        enabled: Boolean(paletId),
        staleTime: 30_000,
        ...options,
    });
}

export function useCreateRafMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createRaf,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.raflar.all });
            queryClient.invalidateQueries({ queryKey: queryKeys.depolar.all });
        },
    });
}
