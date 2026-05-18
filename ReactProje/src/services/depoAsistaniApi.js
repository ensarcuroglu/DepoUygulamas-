import api from './api';

// ---------------------------------------------------------------------------
// Depo Asistani — frontend HTTP istemcisi
// BackendProje /api/asistan/* uclari ile konusur. AssistantAiService'i
// BackendProje proxy'ler; frontend asla AssistantAiService'i dogrudan cagirmaz.
// ---------------------------------------------------------------------------

/**
 * Sohbet mesaji gonder. Eger LLM bir HITL aleti onerirse cevap icinde
 * `taslak` alani dolu doner; frontend taslak kartini render eder.
 */
export const asistanChat = ({
  soru,
  session_id = null,
  aktif_gorev_id = null,
  aktif_ekran = null,
}) =>
  api.post('/asistan/chat', {
    soru,
    session_id,
    aktif_gorev_id,
    aktif_ekran,
  });

export const asistanTaslaklariGetir = ({
  durum = null,
  sadece_kendim = true,
  skip = 0,
  limit = 100,
} = {}) =>
  api.get('/asistan/taslaklar', {
    params: { durum, sadece_kendim, skip, limit },
  });

export const asistanTaslakOnayla = (taslakId, { not_metni = null } = {}) =>
  api.post(`/asistan/taslaklar/${taslakId}/onayla`, { not_metni });

export const asistanTaslakReddet = (taslakId, { sebep = null } = {}) =>
  api.post(`/asistan/taslaklar/${taslakId}/reddet`, { sebep });

export const asistanToolsGetir = () => api.get('/asistan/tools');
