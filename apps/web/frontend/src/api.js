import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export const removeBackground = async (file, options = {}) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('format', options.format || 'png');
  formData.append('quality', options.quality || 95);

  if (options.apiKey) {
    formData.append('api_key', options.apiKey);
  }

  const response = await api.post('/remove-background', formData, {
    responseType: 'blob',
  });

  return response.data;
};

export const removeBackgroundDocument = async (file, options = {}) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('format', options.format || 'png');
  formData.append('quality', options.quality || 95);
  formData.append('ink_threshold', options.inkThreshold !== undefined ? options.inkThreshold : 25.0);
  formData.append('bg_radius', options.bgRadius !== undefined ? options.bgRadius : 30);

  const response = await api.post('/remove-background-document', formData, {
    responseType: 'blob',
  });

  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getUsage = async (apiKey) => {
  const response = await api.get(`/usage?api_key=${apiKey}`);
  return response.data;
};








