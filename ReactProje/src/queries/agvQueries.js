/**
 * TanStack Query hook'ları — AGV REST endpoint'leri.
 *
 * NOT: Yüksek frekanslı robot konumları WS üzerinden zustand'a yazılır
 * (bkz. `hooks/useAgvWebSocket`). Bu dosyadaki query'ler sadece statik/seyrek
 * veriler içindir (grid snapshot, manuel REST yedeği).
 */

import { useQuery } from '@tanstack/react-query';

import { agvApi } from '../services/agvApi';
import { queryKeys } from './queryKeys';

export function useAgvGridQuery(options = {}) {
    return useQuery({
        queryKey: queryKeys.agv.grid(),
        queryFn: agvApi.grid,
        staleTime: Infinity,
        ...options,
    });
}

export function useAgvRobotlarSnapshot(options = {}) {
    return useQuery({
        queryKey: queryKeys.agv.robotlar(),
        queryFn: agvApi.robotlar,
        refetchInterval: 5000,
        ...options,
    });
}
