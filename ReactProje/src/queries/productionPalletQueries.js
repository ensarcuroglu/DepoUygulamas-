import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    createUretimPaleti,
    getUretimPaletleri,
    uretimPaletiIptal,
    uretimPaletiKabulBekle,
    uretimPaletiKabulEt,
    uretimPaletiKarantinaAl,
    uretimPaletiKarantinaCikar,
} from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateProductionPalletData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.uretimPaletleri.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.lotlar.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useUretimPaletleriQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.uretimPaletleri.list(params),
        queryFn: () => getUretimPaletleri(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useCreateUretimPaletiMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createUretimPaleti,
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}

export function useUretimPaletiKabulBekleMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: uretimPaletiKabulBekle,
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}

export function useUretimPaletiKabulEtMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: uretimPaletiKabulEt,
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}

export function useUretimPaletiKarantinaAlMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ paletNo, data }) => uretimPaletiKarantinaAl(paletNo, data),
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}

export function useUretimPaletiKarantinaCikarMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ paletNo, data }) => uretimPaletiKarantinaCikar(paletNo, data),
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}

export function useUretimPaletiIptalMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ paletNo, data }) => uretimPaletiIptal(paletNo, data),
        onSuccess: () => invalidateProductionPalletData(queryClient),
    });
}
