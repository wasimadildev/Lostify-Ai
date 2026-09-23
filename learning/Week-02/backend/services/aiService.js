const axios = require('axios');
const FormData = require('form-data');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

function normalizeWeights(weightImage, weightText, hasImage, hasText) {
  let image = Number.isFinite(Number(weightImage)) ? Number(weightImage) : 0.5;
  let text = Number.isFinite(Number(weightText)) ? Number(weightText) : 0.5;

  if (!hasImage) image = 0;
  if (!hasText) text = 0;
  if (image < 0 || text < 0) throw new Error('Search weights cannot be negative.');

  const total = image + text;
  if (total === 0) throw new Error('At least one image or text query is required.');

  return { image: image / total, text: text / total };
}

async function searchLostItems({
  imageBuffer = null,
  filename = 'image.jpg',
  contentType = 'application/octet-stream',
  text = null,
  weightImage = 0.5,
  weightText = 0.5,
  topK = 5,
} = {}) {
  const normalizedText = typeof text === 'string' ? text.trim() : '';
  const hasImage = Boolean(imageBuffer);
  const hasText = normalizedText.length > 0;
  const weights = normalizeWeights(weightImage, weightText, hasImage, hasText);
  const form = new FormData();

  if (hasImage) {
    form.append('image', imageBuffer, { filename, contentType });
  }
  if (hasText) form.append('text', normalizedText);
  form.append('weight_image', String(weights.image));
  form.append('weight_text', String(weights.text));
  form.append('top_k', String(Math.max(1, Math.min(Number(topK) || 5, 50))));

  try {
    const response = await axios.post(`${AI_SERVICE_URL}/search`, form, {
      headers: form.getHeaders(),
      maxContentLength: 15 * 1024 * 1024,
      maxBodyLength: 15 * 1024 * 1024,
      timeout: 60000,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const detail = error.response.data?.detail || error.response.data;
      throw new Error(`AI service error (${error.response.status}): ${JSON.stringify(detail)}`);
    }
    if (error.request) {
      throw new Error(`AI service unreachable at ${AI_SERVICE_URL}`);
    }
    throw new Error(`AI request failed: ${error.message}`);
  }
}

async function getAiHealth() {
  try {
    const response = await axios.get(`${AI_SERVICE_URL}/health`, { timeout: 5000 });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(`AI service health error (${error.response.status})`);
    }
    throw new Error(`AI service unreachable at ${AI_SERVICE_URL}`);
  }
}

module.exports = { getAiHealth, searchLostItems };
