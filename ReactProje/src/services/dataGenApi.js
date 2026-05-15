import api from './api';

export const getDataGenHealth = () => api.get('/data-gen/healthz');

export const getDataGenMetadata = () => api.get('/data-gen/metadata');

export const postDataGenScenarioRun = ({ name, payload }) =>
  api.post(`/data-gen/scenarios/${name}/run`, payload);
