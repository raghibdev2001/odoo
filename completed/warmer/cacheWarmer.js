const fs = require('fs/promises');
const http = require('http');
const https = require('https');
const { URL } = require('url');

const CONCURRENCY_LIMIT = 500;
const RETRY_LIMIT = 1;

const agents = {
  'http:': new http.Agent({ keepAlive: true, maxSockets: CONCURRENCY_LIMIT }),
  'https:': new https.Agent({ keepAlive: true, maxSockets: CONCURRENCY_LIMIT }),
};

async function loadUrls(file) {
  const raw = await fs.readFile(file, 'utf-8');
  return raw.split(/\r?\n/).filter(line => line.trim().length > 0);
}

function headRequest(url) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const lib = u.protocol === 'https:' ? https : http;

    const req = lib.request({
      method: 'HEAD',
      hostname: u.hostname,
      path: u.pathname + u.search,
      port: u.port,
      agent: agents[u.protocol],
      timeout: 5000,
      headers: {
        'User-Agent': 'CacheWarmer/Node.js',
      },
    }, res => {
      resolve({ url, status: res.statusCode });
    });

    req.on('error', () => resolve({ url, status: 'ERR' }));
    req.on('timeout', () => resolve({ url, status: 'TIMEOUT' }));
    req.end();
  });
}

async function processWithRetries(url, retries = RETRY_LIMIT) {
  let attempt = 0;
  let result;
  while (attempt <= retries) {
    result = await headRequest(url);
    if (typeof result.status === 'number' && result.status >= 200 && result.status < 400) {
      return { url, status: result.status };
    }
    attempt++;
  }
  return { url, status: result.status };
}

async function runWithConcurrency(urls, limit = CONCURRENCY_LIMIT) {
  let index = 0;
  let active = 0;

  return new Promise((resolve) => {
    const results = [];

    const launchNext = () => {
      if (index >= urls.length && active === 0) return resolve(results);

      while (active < limit && index < urls.length) {
        const url = urls[index++];
        active++;
        processWithRetries(url).then(result => {
          results.push(result);
          if (result.status === 200) {
            console.log(`[200] Warmed: ${result.url}`);
          } else {
            console.log(`[ERR] ${result.url} [${result.status}]`);
          }
        }).finally(() => {
          active--;
          launchNext();
        });
      }
    };

    launchNext();
  });
}

(async () => {
  try {
    const urls = await loadUrls('urls.txt');

    console.log(urls);
    console.log(`🚀 Starting warm-up for ${urls.length} URLs with ${CONCURRENCY_LIMIT} concurrency...\n`);
    const start = Date.now();

    await runWithConcurrency(urls, CONCURRENCY_LIMIT);

    const duration = ((Date.now() - start) / 1000).toFixed(2);
    console.log(`✅ Done warming all URLs in ${duration} seconds.`);
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
  }
})();
