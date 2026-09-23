const axios = require('axios');
const FormData = require('form-data');

// Configuration – point to your FastAPI service
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

/**
 * Search for matching lost items using image, text, or both.
 *
 * @param {Object} params
 * @param {Buffer|Stream} params.imageBuffer - Image file buffer/stream (optional)
 * @param {string} params.filename - Original filename (e.g., "query.jpg")
 * @param {string} params.text - Text description (optional)
 * @param {number} params.weightImage - Weight for image similarity (0.0 to 1.0, default 0.5)
 * @param {number} params.weightText - Weight for text similarity (0.0 to 1.0, default 0.5)
 * @param {number} params.topK - Number of results to return (default 5)
 * @returns {Promise<Object>} - Parsed JSON response from AI service
 */
async function searchLostItems({
  imageBuffer = null,
  filename = 'image.jpg',
  text = null,
  weightImage = 0.5,
  weightText = 0.5,
  topK = 5,
} = {}) {
  // Validate: at least one query type provided
  if (!imageBuffer && !text) {
    throw new Error('Must provide either an image or text query.');
  }

  // Auto-adjust weights if only one mode is used
  if (!imageBuffer) weightImage = 0.0;
  if (!text) weightText = 0.0;

  // Normalize weights
  const total = weightImage + weightText;
  if (total === 0) {
    throw new Error('No valid query provided.');
  }
  const finalWeightImage = weightImage / total;
  const finalWeightText = weightText / total;

  // Build multipart form data
  const form = new FormData();

  // Append image if provided
  if (imageBuffer) {
    form.append('image', imageBuffer, {
      filename: filename,
      contentType: 'image/jpeg', // adjust if needed (png, etc.)
    });
  }

  // Append text if provided
  if (text) {
    form.append('text', text);
  }

  // Append weights and topK
  form.append('weight_image', finalWeightImage);
  form.append('weight_text', finalWeightText);
  form.append('top_k', topK);

  // Send request to FastAPI
  try {
    const response = await axios.post(
      `${AI_SERVICE_URL}/search`,
      form,
      {
        headers: {
          ...form.getHeaders(), // important: sets correct Content-Type with boundary
        },
        timeout: 30000, // 30 seconds (CLIP can be slow on CPU)
      }
    );

    return response.data;
  } catch (error) {
    // Forward any error from the AI service
    if (error.response) {
      // The AI service responded with an error status
      throw new Error(`AI Service Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      // No response received from AI service
      throw new Error(`AI Service unreachable: ${error.message}`);
    } else {
      // Something else went wrong
      throw new Error(`Request failed: ${error.message}`);
    }
  }
}

module.exports = { searchLostItems };