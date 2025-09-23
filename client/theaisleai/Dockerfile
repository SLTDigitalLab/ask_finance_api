FROM node:18-alpine as BUILD_IMAGE
WORKDIR /app


COPY package.json .

RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

# FROM nginx:alpine

# COPY --from=BUILD_IMAGE /app/dist /usr/share/nginx/html
# COPY /nginx/nginx.conf /etc/nginx/nginx.conf

# # RUN useradd -ms /bin/bash www-data
# # RUN chown -R www-data:www-data /usr/share/nginx/html

# EXPOSE 80

# CMD ["nginx","-g","daemon off;"]