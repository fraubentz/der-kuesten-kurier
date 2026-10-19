import http from 'http';
import fs from 'fs';
import path from 'path';

const PORT = 3000;
const HOST = '0.0.0.0';
const DOCS_DIR = path.resolve('docs');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  let reqPath = decodeURI(req.url.split('?')[0]);
  if (reqPath === '/' || reqPath === '') {
    reqPath = '/index.html';
  }

  let filePath = path.join(DOCS_DIR, reqPath);

  // Security check: ensure path does not escape DOCS_DIR
  if (!filePath.startsWith(DOCS_DIR)) {
    res.statusCode = 403;
    res.end('Forbidden');
    return;
  }

  // Handle directory index
  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
    filePath = path.join(filePath, 'index.html');
  }

  if (!fs.existsSync(filePath)) {
    res.statusCode = 404;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end('<h1>404 – Ausgabe oder Seite nicht gefunden</h1><p><a href="/">Zurück zur aktuellen Ausgabe</a></p>');
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';
  res.writeHead(200, {
    'Content-Type': contentType,
    'Cache-Control': 'no-cache',
  });

  fs.createReadStream(filePath).pipe(res);
});

server.listen(PORT, HOST, () => {
  console.log(`Der Küsten-Kurier läuft auf http://${HOST}:${PORT}`);
});