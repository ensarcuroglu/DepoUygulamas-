import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteLot, getLotlar, getSktYaklasanLotlar } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const lotListData = (response) => ({
    data: responseData(response),
    totalCount: Number(response?.headers?.['x-total-count'] || 0),
});

const invalidateLotData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.lotlar.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.urunler.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useLotlarQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.lotlar.list(params),
        queryFn: () => getLotlar(params).then(lotListData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useSktYaklasanLotlarQuery(gun = 30, options = {}) {
    return useQuery({
        queryKey: queryKeys.lotlar.sktYaklasan(gun),
        queryFn: () => getSktYaklasanLotlar(gun).then(responseData),
        ...options,
    });
}

export function useDeleteLotMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteLot,
        onSuccess: () => invalidateLotData(queryClient),
    });
}
