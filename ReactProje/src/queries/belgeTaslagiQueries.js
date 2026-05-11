import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    getBelgeIncelemeKuyrugu,
    getBelgeTaslagi,
    getBelgeTaslaklari,
    onaylaBelgeTaslagi,
    reddetBelgeTaslagi,
    uploadBelgeTaslagi,
} from '../services/belgeTaslagiApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateBelgeTaslagiData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.belgeTaslaklari.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.malKabulIrsaliyeleri.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
};

export function useBelgeTaslaklariQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.belgeTaslaklari.list(params),
        queryFn: () => getBelgeTaslaklari(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useBelgeTaslagiQuery(id, options = {}) {
    return useQuery({
        queryKey: queryKeys.belgeTaslaklari.detail(id),
        queryFn: () => getBelgeTaslagi(id).then(responseData),
        enabled: Boolean(id),
        ...options,
    });
}

export function useBelgeIncelemeKuyruguQuery(params = {}, options = {}) {
    return useQuery({
        queryKey: queryKeys.belgeTaslaklari.reviewQueue(params),
        queryFn: () => getBelgeIncelemeKuyrugu(params).then(responseData),
        placeholderData: (previousData) => previousData,
        ...options,
    });
}

export function useBelgeYukleMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: uploadBelgeTaslagi,
        onSuccess: () => invalidateBelgeTaslagiData(queryClient),
    });
}

export function useBelgeTaslagiOnaylaMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data, idempotencyKey }) =>
            onaylaBelgeTaslagi(id, data, idempotencyKey),
        onSuccess: () => invalidateBelgeTaslagiData(queryClient),
    });
}

export function useBelgeTaslagiReddetMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data, idempotencyKey }) =>
            reddetBelgeTaslagi(id, data, idempotencyKey),
        onSuccess: () => invalidateBelgeTaslagiData(queryClient),
    });
}
