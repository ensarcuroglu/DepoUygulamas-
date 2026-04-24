import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    createMalKabulIrsaliye,
    deleteMalKabulIrsaliye,
    getMalKabulIrsaliyeleri,
    getTedarikciler,
    malKabulKalemiIstisnaGuncelle,
    onaylaMalKabulIrsaliye,
    updateMalKabulIrsaliye,
} from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateMalKabulData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.malKabulIrsaliyeleri.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.lotlar.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.urunler.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useMalKabulIrsaliyeleriQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.malKabulIrsaliyeleri.list(params),
        queryFn: () => getMalKabulIrsaliyeleri(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useTedarikcilerQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.tedarikciler.list(params),
        queryFn: () => getTedarikciler(params).then(responseData),
        ...options,
    });
}

export function useCreateMalKabulIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createMalKabulIrsaliye,
        onSuccess: () => invalidateMalKabulData(queryClient),
    });
}

export function useUpdateMalKabulIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateMalKabulIrsaliye(id, data),
        onSuccess: () => invalidateMalKabulData(queryClient),
    });
}

export function useDeleteMalKabulIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteMalKabulIrsaliye,
        onSuccess: () => invalidateMalKabulData(queryClient),
    });
}

export function useOnaylaMalKabulIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: onaylaMalKabulIrsaliye,
        onSuccess: () => invalidateMalKabulData(queryClient),
    });
}

export function useMalKabulKalemiIstisnaGuncelleMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ irsaliyeId, kalemId, data }) =>
            malKabulKalemiIstisnaGuncelle(irsaliyeId, kalemId, data),
        onSuccess: () => invalidateMalKabulData(queryClient),
    });
}
