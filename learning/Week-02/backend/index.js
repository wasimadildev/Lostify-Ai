require('dotenv').config();

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { getAiHealth, searchLostItems } = require('./services/aiService');

const app = express();
const port = Number(process.env.PORT) || 3000;
const dataDirectory = path.join(__dirname, 'data');
const uploadsDirectory = path.join(__dirname, 'uploads');
const reportsPath = path.join(dataDirectory, 'reports.json');

for (const directory of [dataDirectory, uploadsDirectory]) {
  fs.mkdirSync(directory, { recursive: true });
}
if (!fs.existsSync(reportsPath)) fs.writeFileSync(reportsPath, '[]');

app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use('/uploads', express.static(uploadsDirectory));

const allowedImageTypes = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif']);
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (request, file, callback) => {
    if (!allowedImageTypes.has(file.mimetype)) {
      return callback(new Error('Only JPEG, PNG, WEBP, and GIF images are supported.'));
    }
    callback(null, true);
  },
});

function readReports() {
  return JSON.parse(fs.readFileSync(reportsPath, 'utf8'));
}

function writeReports(reports) {
  fs.writeFileSync(reportsPath, JSON.stringify(reports, null, 2));
}

function requiredText(value, fieldName) {
  if (typeof value !== 'string' || value.trim() === '') {
    const error = new Error(`${fieldName} is required.`);
    error.statusCode = 400;
    throw error;
  }
  return value.trim();
}

function safeExtension(file) {
  const extension = path.extname(file.originalname || '').toLowerCase();
  return extension || '.jpg';
}

app.get('/', (request, response) => {
  response.json({
    service: 'Lostify Node.js Backend',
    status: 'online',
    endpoints: ['GET /health', 'GET /api/health', 'POST /api/search', 'POST /api/reports', 'GET /api/reports'],
  });
});

app.get(['/health', '/api/health'], async (request, response) => {
  try {
    const ai = await getAiHealth();
    response.json({ status: 'healthy', backend: 'online', ai });
  } catch (error) {
    response.status(503).json({ status: 'degraded', backend: 'online', ai: { status: 'unavailable' }, error: error.message });
  }
});

app.post('/api/search', upload.single('image'), async (request, response, next) => {
  try {
    const result = await searchLostItems({
      imageBuffer: request.file?.buffer || null,
      filename: request.file?.originalname || 'query.jpg',
      contentType: request.file?.mimetype || 'application/octet-stream',
      text: request.body.text || null,
      weightImage: request.body.weight_image,
      weightText: request.body.weight_text,
      topK: request.body.top_k,
    });

    response.json({ success: true, data: result });
  } catch (error) {
    next(error);
  }
});

app.post('/api/reports', upload.single('image'), (request, response, next) => {
  try {
    const title = requiredText(request.body.title, 'title');
    const description = requiredText(request.body.description, 'description');
    const category = requiredText(request.body.category, 'category');
    const location = requiredText(request.body.location, 'location');
    const now = new Date().toISOString();
    const reportId = `report-${crypto.randomUUID()}`;
    let imageUrl = null;

    if (request.file) {
      const filename = `${reportId}${safeExtension(request.file)}`;
      fs.writeFileSync(path.join(uploadsDirectory, filename), request.file.buffer);
      imageUrl = `/uploads/${filename}`;
    }

    const report = {
      id: reportId,
      type: 'lost',
      title,
      description,
      category,
      location,
      contactName: request.body.contact_name?.trim() || null,
      contactEmail: request.body.contact_email?.trim() || null,
      imageUrl,
      createdAt: now,
      updatedAt: now,
    };
    

    const reports = readReports();
    reports.unshift(report);
    writeReports(reports);
    response.status(201).json({ success: true, data: report });
  } catch (error) {
    next(error);
  }
});

app.get('/api/reports', (request, response, next) => {
  try {
    const reports = readReports();
    const query = request.query.q?.toString().trim().toLowerCase();
    const filtered = query
      ? reports.filter((report) => [report.title, report.description, report.category, report.location]
          .some((value) => value.toLowerCase().includes(query)))
      : reports;

    response.json({ success: true, count: filtered.length, data: filtered });
  } catch (error) {
    next(error);
  }
});

app.use((error, request, response, next) => {
  if (response.headersSent) return next(error);
  const statusCode = error.statusCode || (error instanceof multer.MulterError ? 400 : 500);
  response.status(statusCode).json({ success: false, error: error.message || 'Internal server error.' });
});

app.listen(port, () => {
  console.log(`Lostify backend listening at http://localhost:${port}`);
});

module.exports = app;
