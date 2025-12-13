# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies (cache layer)
COPY package.json package-lock.json ./
# If no lock file exists, npm install will generate one, but it's better to copy if it exists.
# We'll just copy package.json for now as we saw it.
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Copy build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
