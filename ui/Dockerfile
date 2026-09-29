FROM node:22 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npx ng build

FROM nginx:alpine
COPY --from=build /app/dist/runpulse/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
