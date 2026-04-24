import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createKategori, deleteKategori, getKategoriler, updateKategori } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateCategoryData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.kategoriler.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.urunler.all });
};

export function useKategorilerQuery(options = {}) {
    return useQuery({
        queryKey: queryKeys.kategoriler.list(),
        queryFn: () => getKategoriler().then(responseData),
        staleTime: 0,
        ...options,
    });
}

export function useCreateKategoriMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createKategori,
        onSuccess: () => invalidateCategoryData(queryClient),
    });
}

export function useUpdateKategoriMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateKategori(id, data),
        onSuccess: () => invalidateCategoryData(queryClient),
    });
}

export function useDeleteKategoriMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteKategori,
        onSuccess: () => invalidateCategoryData(queryClient),
    });
}
