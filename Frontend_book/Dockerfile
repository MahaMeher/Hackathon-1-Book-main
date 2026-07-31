# =============================================================================
# Frontend — Docusaurus static site built & served via nginx
# =============================================================================

# --- Stage 1: Build ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# --- Stage 2: Serve via nginx ---
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html

# Custom nginx config: proxy /api to the backend container
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
