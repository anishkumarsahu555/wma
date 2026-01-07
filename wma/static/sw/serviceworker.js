// ================== CONFIG ================== //

// Version / cache name
const CACHE_VERSION = 'WMA-v1';
const CACHE_NAME = `${CACHE_VERSION}::fundamentals`;
const MAX_CACHE_ITEMS = 100;  // limit number of cached items
const MAX_RETRIES = 4;        // limit retries for failed requests

// URLs to pre-cache (fill as needed)
const URLS_TO_CACHE = [
    // '/',
    // '/static/css/app.css',
    // '/static/js/app.js',
];

// File extensions that are cacheable
const CACHEABLE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'svg', 'css', 'js'];

// URL patterns where we DO NOT want SW handling (no cache, no retry)
const NO_RETRY_URL_PATTERNS = [
    /\/attendance\/generate_attendance_report\/.*/,
    /\/invoice\/generate_net_report_accountant\/.*/,
    // add more patterns here if needed
];

// ================== INSTALL ================== //

self.addEventListener('install', (event) => {
    console.log('WORKER: Install event in progress.');

    // Activate this SW immediately (no waiting for old one to die)
    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('WORKER: Caching assets...', URLS_TO_CACHE);
                return cache.addAll(URLS_TO_CACHE);
            })
            .then(() => {
                console.log('WORKER: Install completed.');
            })
            .catch((error) => {
                console.error('WORKER: Failed to cache assets:', error);
            })
    );
});

// ================== ACTIVATE ================== //

self.addEventListener('activate', (event) => {
    console.log('WORKER: Activate event in progress.');

    event.waitUntil(
        (async () => {
            // Take control of open clients (tabs) immediately
            await self.clients.claim();

            // Remove old caches
            const keys = await caches.keys();
            await Promise.all(
                keys
                    .filter((key) => !key.startsWith(CACHE_VERSION))
                    .map((key) => {
                        console.log(`WORKER: Deleting old cache ${key}`);
                        return caches.delete(key);
                    })
            );

            console.log('WORKER: Activate completed. Old caches removed.');
        })().catch((error) => {
            console.error('WORKER: Failed during activate:', error);
        })
    );
});

// ================== FETCH ================== //

self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Only handle GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Ignore third-party origins (GA, fonts, CDNs, etc.)
    if (url.origin !== self.location.origin) {
        // Let the browser handle it normally – no cache, no retry
        return;
    }

    // Bypass SW for long-running / special endpoints (like PDF reports)
    if (NO_RETRY_URL_PATTERNS.some((pattern) => pattern.test(url.pathname))) {
        console.log(`WORKER: Bypassing SW for ${url.pathname}`);
        return; // browser will do normal network request
    }

    // For everything else, use cache + retry logic
    event.respondWith(handleFetchWithRetry(event, request));
});

// ================== CORE LOGIC ================== //

async function handleFetchWithRetry(event, request, retries = 0) {
    try {
        // 1. Try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log(`WORKER: Serving from cache: ${request.url}`);
            // Update cache in background
            event.waitUntil(updateCache(request));
            return cachedResponse;
        }

        // 2. If not in cache, go to network (with timeout)
        const networkResponse = await fetchWithTimeout(request);
        console.log(`WORKER: Fetched from network: ${request.url}`);

        // 3. Cache static assets if cacheable
        if (isCacheable(networkResponse, request.url)) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, networkResponse.clone());
            console.log(`WORKER: Cached response for: ${request.url}`);
            await enforceCacheSizeLimit(cache);
        }

        return networkResponse;

    } catch (error) {
        console.error(
            `WORKER: Fetch attempt ${retries + 1} failed for ${request.url}:`,
            error
        );

        // Retry with exponential backoff (limited)
        if (retries < MAX_RETRIES) {
            const retryDelay = Math.pow(2, retries) * 500; // 500, 1000, 2000, 4000 ms
            console.log(
                `WORKER: Retrying fetch for ${request.url} in ${retryDelay}ms...`
            );
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve(handleFetchWithRetry(event, request, retries + 1));
                }, retryDelay);
            });
        }

        console.error('WORKER: Fetch request failed after maximum retries.');
        // Final fallback response
        return new Response(
            `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Service Unavailable</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f8f9fa;
                        color: #333;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .container {
                        text-align: center;
                        max-width: 600px;
                        padding: 20px;
                        background-color: #fff;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        border-radius: 8px;
                    }
                    h1 {
                        font-size: 24px;
                        color: #d9534f;
                        margin-bottom: 16px;
                    }
                    p {
                        font-size: 16px;
                        color: #555;
                    }
                    ul {
                        text-align: left;
                        display: inline-block;
                        margin-top: 10px;
                    }
                    .button {
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        font-size: 16px;
                        color: #fff;
                        background-color: #007bff;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        transition: background-color 0.3s;
                    }
                    .button:hover {
                        background-color: #0056b3;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Service Unavailable</h1>
                    <p>Oops! It seems there was a problem retrieving the content. Please try the following:</p>
                    <ul>
                        <li>Check your internet connection.</li>
                        <li>Refresh the page in a few moments.</li>
                        <li>Contact support if the problem persists.</li>
                    </ul>
                    <button class="button" onclick="location.reload()">Try Again</button>
                </div>
            </body>
            </html>
        `,
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({ 'Content-Type': 'text/html' }),
            }
        );
    }
}

// ================== HELPERS ================== //

function isCacheable(response, url) {
    const extension = getUrlExtension(url).toLowerCase();
    const scheme = new URL(url).protocol;

    return (
        (scheme === 'http:' || scheme === 'https:') &&
        CACHEABLE_EXTENSIONS.includes(extension)
    );
}

function getUrlExtension(url) {
    return typeof url === 'string'
        ? url.split(/[#?]/)[0].split('.').pop().trim()
        : '';
}

// Fetch with timeout (short to avoid hanging requests)
function fetchWithTimeout(request, timeout = 20000) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(
            () => reject(new Error('Request timed out')),
            timeout
        );

        fetch(request).then(
            (response) => {
                clearTimeout(timer);
                resolve(response);
            },
            (err) => {
                clearTimeout(timer);
                reject(err);
            }
        );
    });
}

// Update cache in background
async function updateCache(request) {
    try {
        const response = await fetchWithTimeout(request);
        if (response && isCacheable(response, request.url)) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, response.clone());
            console.log(`WORKER: Updated cache for ${request.url}`);
            await enforceCacheSizeLimit(cache);
        }
    } catch (error) {
        console.error(`WORKER: Failed to update cache for ${request.url}:`, error);
    }
}

// Enforce cache size limit (simple FIFO)
async function enforceCacheSizeLimit(cache) {
    const keys = await cache.keys();
    if (keys.length > MAX_CACHE_ITEMS) {
        console.log(
            `WORKER: Cache size exceeded ${MAX_CACHE_ITEMS}. Removing oldest item.`
        );
        await cache.delete(keys[0]);
    }
}