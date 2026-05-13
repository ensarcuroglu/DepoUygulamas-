import api from './api';

export const aiSorgula = ({ soru, session_id = null, debug = true, verbose = false }) =>
  api.post('/ai/sorgula', { soru, session_id, debug, verbose });

export const aiChat = ({ soru, session_id = null, debug = true, verbose = false }) =>
  api.post('/ai/chat', { soru, session_id, debug, verbose });

export const aiOturumSifirla = (session_id) =>
  api.post('/ai/oturum/sifirla', { session_id });

export const getAiSema = () => api.get('/ai/sema');
