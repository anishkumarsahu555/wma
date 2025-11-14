var version = 'v1.0.3::';

// Install Event
self.addEventListener("install", (event) => {
    console.log('WORKER: Install event in progress.');
    event.waitUntil(
        caches.open(version + 'fundamentals').then((cache) => {
            return cache.addAll([
                'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/fomantic-ui/2.9.4/semantic.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/fomantic-ui/2.9.4/semantic.min.js',
                'https://cdn.datatables.net/2.3.2/css/dataTables.semanticui.min.css',
                'https://cdn.datatables.net/2.3.2/js/dataTables.min.js',
                'https://cdn.datatables.net/2.3.2/js/dataTables.semanticui.min.js',
                'https://cdn.datatables.net/buttons/3.2.4/js/dataTables.buttons.min.js',
                'https://cdn.datatables.net/buttons/3.2.4/js/buttons.semanticui.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js',
                'https://cdn.datatables.net/buttons/3.2.4/js/buttons.html5.min.js',
                'https://cdn.datatables.net/buttons/3.2.4/js/buttons.print.min.js',
                'https://cdn.datatables.net/buttons/3.2.4/js/buttons.colVis.min.js',
                'https://fonts.googleapis.com/css?family=Lato:400,700,400italic,700italic&subset=latin'
            ]);
        }).then(() => console.log('WORKER: Install completed.'))
    );
});

// Activate Event
self.addEventListener("activate", (event) => {
    console.log('WORKER: Activate event in progress.');
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => !key.startsWith(version))
                    .map((key) => caches.delete(key))
            );
        }).then(() => console.log('WORKER: Activate completed.'))
    );
});

// Helper to get file extension
function getUrlExtension(url) {
    return url.split(/[#?]/)[0].split('.').pop().trim();
}

// Fetch Event
self.addEventListener("fetch", (event) => {
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then((cached) => {
            const fetchPromise = fetch(event.request)
                .then((networkResponse) => {
                    // Cache images and pages dynamically
                    caches.open(version + 'pages').then((cache) => {
                        const ext = getUrlExtension(event.request.url).toLowerCase();
                        if (['png','jpg','jpeg','svg','html'].includes(ext)) {
                            cache.put(event.request, networkResponse.clone());
                        }
                    });
                    return networkResponse;
                })
                .catch(() => cached || offlineResponse());

            return cached || fetchPromise;
        })
    );
});

// Offline fallback
function offlineResponse() {
    const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Offline</title>
      <style>
        body { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0; font-family:"Segoe UI",sans-serif; background:linear-gradient(135deg,#193038,#2d3e50); color:#fff; text-align:center;}
        h1{font-size:2rem; margin-bottom:.5rem;} p{margin-bottom:1.5rem; opacity:.9;}
        .spinner{border:6px solid rgba(255,255,255,0.2); border-top:6px solid #ff6b6b; border-radius:50%; width:50px; height:50px; animation:spin 1s linear infinite; margin:20px auto;}
        @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
        button{background:#ff6b6b; border:none; padding:12px 20px; font-size:1rem; font-weight:bold; border-radius:8px; cursor:pointer; transition:background 0.3s;}
        button:hover{background:#ff3b3b;}
        #toast{visibility:hidden; min-width:250px; background-color:#4CAF50; color:#fff; text-align:center; border-radius:8px; padding:16px; position:fixed; z-index:1; left:50%; bottom:30px; transform:translateX(-50%); font-size:1rem; opacity:0; transition:opacity 0.5s,bottom 0.5s;}
        #toast.show{visibility:visible; opacity:1; bottom:50px;}
      </style>
    </head>
    <body>
      <h1>⚠ You’re Offline</h1>
      <p>Trying to reconnect... Please check your internet connection.</p>
      <div class="spinner"></div>
      <button onclick="window.location.reload()">🔄 Reload Now</button>
      <div id="toast">🎉 Back Online!</div>
      <script>
        function showToast(){const t=document.getElementById("toast");t.classList.add("show");setTimeout(()=>t.classList.remove("show"),4000);}
        setInterval(()=>{fetch(window.location.href,{method:'HEAD',cache:'no-store'}).then(()=>{showToast();setTimeout(()=>window.location.reload(),1500);}).catch(()=>console.log("Still offline..."));},5000);
      </script>
    </body>
    </html>
  `;
    return new Response(html, { headers: { 'Content-Type': 'text/html' } });
}