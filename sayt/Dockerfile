FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html i18n.js support.js logo.html /usr/share/nginx/html/
COPY images /usr/share/nginx/html/images
EXPOSE 80
