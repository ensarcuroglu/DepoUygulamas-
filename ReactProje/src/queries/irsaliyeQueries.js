import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    createIrsaliye,
    getIrsaliyeler,
    getSevkiyatPlanlari,
    getSiparisler,
    updateIrsaliye,
} from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateIrsaliyeData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.irsaliyeler.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.sevkiyatPlanlari.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useIrsaliyelerQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.irsaliyeler.list(params),
        queryFn: () => getIrsaliyeler(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useSiparislerQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.siparisler.list(params),
        queryFn: () => getSiparisler(params).then(responseData),
        ...options,
    });
}

export function useSevkiyatPlanlariQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.sevkiyatPlanlari.list(params),
        queryFn: () => getSevkiyatPlanlari(params).then(responseData),
        ...options,
    });
}

export function useCreateIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createIrsaliye,
        onSuccess: () => invalidateIrsaliyeData(queryClient),
    });
}

export function useUpdateIrsaliyeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateIrsaliye(id, data),
        onSuccess: () => invalidateIrsaliyeData(queryClient),
    });
}
