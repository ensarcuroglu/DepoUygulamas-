import api from './api';

export const getExcelAiHedefSemalar = () => api.get('/excel-ai/hedef-semalar');

export const postExcelAiYorumla = ({ file, soru, sheet_name, idempotencyKey }) => {
  const form = new FormData();
  form.append('file', file);
  if (soru) form.append('soru', soru);
  if (sheet_name) form.append('sheet_name', sheet_name);
  return api.post('/excel-ai/yorumla', form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    },
  });
};

export const postExcelAiSemaEsle = ({ file, hedef_sema, sheet_name, idempotencyKey }) => {
  const form = new FormData();
  form.append('file', file);
  form.append('hedef_sema', hedef_sema);
  if (sheet_name) form.append('sheet_name', sheet_name);
  return api.post('/excel-ai/sema-esle', form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    },
  });
};
