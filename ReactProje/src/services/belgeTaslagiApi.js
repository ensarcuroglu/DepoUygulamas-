import api from './api';

export const createBelgeTaslagiIdempotencyKey = (prefix = 'doc-ai') => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return `${prefix}-${crypto.randomUUID()}`;
    }

    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const uploadBelgeTaslagi = ({
    depoId,
    file,
    idempotencyKey = createBelgeTaslagiIdempotencyKey('upload'),
    onUploadProgress,
}) => {
    const formData = new FormData();
    formData.append('depo_id', String(depoId));
    formData.append('file', file);

    return api.post('/mal-kabul/belge-yukle', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
            'Idempotency-Key': idempotencyKey,
        },
        onUploadProgress,
    });
};

export const getBelgeTaslaklari = (params = {}) =>
    api.get('/belge-taslaklari/', { params });

export const getBelgeIncelemeKuyrugu = (params = {}) =>
    api.get('/belge-taslaklari/inceleme-kuyrugu', { params });

export const getBelgeTaslagi = (id) =>
    api.get(`/belge-taslaklari/${id}`);

export const onaylaBelgeTaslagi = (
    id,
    data,
    idempotencyKey = createBelgeTaslagiIdempotencyKey('approve'),
) =>
    api.post(`/belge-taslaklari/${id}/onayla`, data, {
        headers: {
            'Idempotency-Key': idempotencyKey,
        },
    });

export const reddetBelgeTaslagi = (
    id,
    data,
    idempotencyKey = createBelgeTaslagiIdempotencyKey('reject'),
) =>
    api.post(`/belge-taslaklari/${id}/reddet`, data, {
        headers: {
            'Idempotency-Key': idempotencyKey,
        },
    });
