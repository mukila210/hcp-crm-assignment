import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({ baseURL: API_BASE });

export async function submitInteraction(form) {
  const { data } = await client.post('/api/interactions', form);
  return data;
}

export async function sendChatTurn(payload) {
  const { data } = await client.post('/api/chat/turn', payload);
  return data;
}

export async function confirmChatInteraction(sessionId, hcpId, fieldRepId) {
  const { data } = await client.post(
    `/api/chat/${sessionId}/confirm`,
    null,
    { params: { hcp_id: hcpId, field_rep_id: fieldRepId } }
  );
  return data;
}
