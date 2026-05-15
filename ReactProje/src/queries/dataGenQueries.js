import { useMutation, useQuery } from '@tanstack/react-query';
import {
  getDataGenHealth,
  getDataGenMetadata,
  postDataGenScenarioRun,
} from '../services/dataGenApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useDataGenHealthQuery({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.dataGen.health(),
    queryFn: () => getDataGenHealth().then(responseData),
    staleTime: 1000 * 15,
    retry: 1,
    enabled,
  });
}

export function useDataGenMetadataQuery({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.dataGen.metadata(),
    queryFn: () => getDataGenMetadata().then(responseData),
    staleTime: 1000 * 60 * 30,
    enabled,
  });
}

export function useDataGenRunScenarioMutation() {
  return useMutation({
    mutationFn: ({ name, payload }) =>
      postDataGenScenarioRun({ name, payload }).then(responseData),
  });
}
