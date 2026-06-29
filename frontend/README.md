# LocustHub Admin

Stage 4 introduces a Vue 3 + Vite + TypeScript management console inspired by
the Vben Admin layout model.

```bash
cd frontend
npm install --registry=https://registry.npmjs.org/
npm run dev
npm run build
```

The dev server uses `http://127.0.0.1:5173` and calls the FastAPI backend at
`http://127.0.0.1:8000/api/v1` by default.

Environment overrides:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_DEMO_TOKEN=dev-token
```

`npm run build` uses `scripts/build.mjs` to call the Vite API directly. The
local Node 18.8 environment can hang in the Vite CLI minifier path, so Stage 4
keeps minification disabled and leaves production compression to Nginx/CDN.

## Container

Stage 6 adds `frontend/Dockerfile` and `frontend/nginx.conf` for the deployable
admin console image. The image builds the static Vite bundle and serves it with
Nginx. In Docker Compose, `/api/` is proxied to the `api` service so the browser
can call `/api/v1` without hard-coding an internal container hostname.
