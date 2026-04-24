import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createKullanici, deleteKullanici, getKullanicilar, updateKullanici } from '../services/api';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

const invalidateUserData = (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.kullanicilar.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
};

export function useKullanicilarQuery(options = {}) {
    return useQuery({
        queryKey: queryKeys.kullanicilar.list(),
        queryFn: () => getKullanicilar().then(responseData),
        ...options,
    });
}

export function useCreateKullaniciMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createKullanici,
        onSuccess: () => invalidateUserData(queryClient),
    });
}

export function useUpdateKullaniciMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => updateKullanici(id, data),
        onSuccess: () => invalidateUserData(queryClient),
    });
}

export function useDeleteKullaniciMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteKullanici,
        onSuccess: () => invalidateUserData(queryClient),
    });
}
