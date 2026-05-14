import { useMutation, useQuery } from '@tanstack/react-query';
import {
  getExcelAiHedefSemalar,
  postExcelAiYorumla,
  postExcelAiSemaEsle,
} from '../services/excelAiApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

export function useExcelAiHedefSemalarQuery({ enabled = true } = {}) {
  return useQuery({
    queryKey: queryKeys.excelAi.hedefSemalar(),
    queryFn: () => getExcelAiHedefSemalar().then(responseData),
    staleTime: 1000 * 60 * 60,
    enabled,
  });
}

export function useExcelAiYorumlaMutation() {
  return useMutation({
    mutationFn: (payload) => postExcelAiYorumla(payload).then(responseData),
  });
}

export function useExcelAiSemaEsleMutation() {
  return useMutation({
    mutationFn: (payload) => postExcelAiSemaEsle(payload).then(responseData),
  });
}
