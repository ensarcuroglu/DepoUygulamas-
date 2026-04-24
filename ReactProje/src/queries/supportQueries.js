import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createDestekTalebi, getDestekTalepleri, updateDestekTalebi } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateSupportData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.destek.all });
};

export function useDestekTalepleriQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.destek.list(params),
        queryFn: () => getDestekTalepleri(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useCreateDestekTalebiMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createDestekTalebi,
        onSuccess: () => invalidateSupportData(queryClient),
    });
}

export function useUpdateDestekTalebiMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateDestekTalebi(id, data),
        onSuccess: () => invalidateSupportData(queryClient),
    });
}
