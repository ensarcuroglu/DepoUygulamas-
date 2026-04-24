import { QueryClient } from '@tanstack/react-query';

const noRetryStatuses = new Set([400, 401, 403, 404, 409, 422]);

const shouldRetryQuery = (failureCount, error) => {
    if (failureCount >= 1) return false;

    const status = error?.response?.status ?? error?.status;
    if (noRetryStatuses.has(status)) return false;

    return status === 0 || !status || status >= 500;
};

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            refetchOnWindowFocus: false,
            retry: shouldRetryQuery,
        },
        mutations: {
            retry: false,
        },
    },
});

export default queryClient;
