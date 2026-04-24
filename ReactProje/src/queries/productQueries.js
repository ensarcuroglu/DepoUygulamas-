import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    createUrun,
    deleteUrun,
    getMarkalar,
    getUrunler,
    updateUrun,
} from '../services/api';
import { urunStokDetayApi } from '../services/paletRezervasyonlariApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export { useKategorilerQuery } from './categoryQueries';

const invalidateProductData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.urunler.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useUrunlerQuery(params) {
    return useQuery({
        queryKey: queryKeys.urunler.list(params),
        queryFn: () => getUrunler(params).then(responseData),
        placeholderData: (previousData) => previousData,
    });
}

export function useMarkalarQuery() {
    return useQuery({
        queryKey: queryKeys.markalar.list(),
        queryFn: () => getMarkalar().then(responseData),
        staleTime: 5 * 60_000,
    });
}

export function useUrunStokDetayQuery(urunId, enabled) {
    return useQuery({
        queryKey: queryKeys.urunler.stockDetail(urunId),
        queryFn: () => urunStokDetayApi.getir(urunId),
        enabled: Boolean(enabled && urunId),
    });
}

export function useCreateUrunMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createUrun,
        onSuccess: () => invalidateProductData(queryClient),
    });
}

export function useUpdateUrunMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateUrun(id, data),
        onSuccess: () => invalidateProductData(queryClient),
    });
}

export function useDeleteUrunMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteUrun,
        onSuccess: () => invalidateProductData(queryClient),
    });
}
