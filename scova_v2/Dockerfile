# uploaditin_v2/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Salin package files & install dependencies
COPY package*.json ./
RUN npm ci

# Salin semua kode sumber
COPY . .

# Salin .env.production agar NEXT_PUBLIC_* tersedia saat build
# (Next.js inline NEXT_PUBLIC_* ke dalam client bundle saat `next build`)
COPY .env.production .env.production

# ARG bisa override dari docker-compose build args (opsional)
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_KEY
ARG NEXT_PUBLIC_BACKEND_URL
ARG BACKEND_URL=http://backend:5000

# Set runtime ENV (untuk server-side & rewrites)
ENV BACKEND_URL=$BACKEND_URL

# Jika ARG diberikan, set sebagai ENV agar next build menggunakannya
# Jika tidak, next build akan membaca dari .env.production
RUN if [ -n "$NEXT_PUBLIC_SUPABASE_URL" ]; then \
      echo "NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL" >> .env.production; \
    fi && \
    if [ -n "$NEXT_PUBLIC_SUPABASE_KEY" ]; then \
      echo "NEXT_PUBLIC_SUPABASE_KEY=$NEXT_PUBLIC_SUPABASE_KEY" >> .env.production; \
    fi && \
    if [ -n "$NEXT_PUBLIC_BACKEND_URL" ]; then \
      echo "NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL" >> .env.production; \
    fi

# Build aplikasi Next.js (NEXT_PUBLIC_* akan di-inline ke client JS)
RUN npm run build

# Port default Next.js
EXPOSE 3000

# Jalankan aplikasi
CMD ["npm", "start"]
