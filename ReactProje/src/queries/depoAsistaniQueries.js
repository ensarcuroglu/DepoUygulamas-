import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  asistanChat,
  asistanTaslakOnayla,
  asistanTaslakReddet,
  asistanTaslaklariGetir,
  asistanToolsGetir,
} from '../services/depoAsistaniApi';
import { queryKeys } from './queryKeys';
import { responseData } from './queryUtils';

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export function useDepoAsistaniChatMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload) => asistanChat(payload).then(responseData),
    onSuccess: (data) => {
      // Backend HITL onerirse, taslak listesi degisti — invalidate et.
      if (data?.taslak) {
        qc.invalidateQueries({ queryKey: queryKeys.depoAsistani.taslaklar() });
      }
    },
  });
}

// ---------------------------------------------------------------------------
// Taslaklar — listele
// ---------------------------------------------------------------------------

export function useDepoAsistaniTaslaklariQuery(params = {}, options = {}) {
  return useQuery({
    queryKey: queryKeys.depoAsistani.taslaklarList(params),
    queryFn: () => asistanTaslaklariGetir(params).then(responseData),
    staleTime: 1000 * 30,
    ...options,
  });
}

// ---------------------------------------------------------------------------
// Taslak — onayla / reddet
// ---------------------------------------------------------------------------

export function useDepoAsistaniTaslakOnaylaMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, not_metni }) =>
      asistanTaslakOnayla(id, { not_metni }).then(responseData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.depoAsistani.taslaklar() });
    },
  });
}

export function useDepoAsistaniTaslakReddetMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, sebep }) =>
      asistanTaslakReddet(id, { sebep }).then(responseData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.depoAsistani.taslaklar() });
    },
  });
}

// ---------------------------------------------------------------------------
// Tools meta (frontend gosterimi icin opsiyonel)
// ---------------------------------------------------------------------------

export function useDepoAsistaniToolsQuery(options = {}) {
  return useQuery({
    queryKey: queryKeys.depoAsistani.tools(),
    queryFn: () => asistanToolsGetir().then(responseData),
    staleTime: 1000 * 60 * 10,
    ...options,
  });
}
