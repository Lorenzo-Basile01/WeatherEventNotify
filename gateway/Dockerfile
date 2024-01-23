FROM nginx:1.24-bullseye

RUN rm /etc/nginx/conf.d/default.conf
COPY routing.conf /etc/nginx/conf.d/routing.conf
RUN sed -i '/security/d' /etc/apt/sources.list && \
    sed -i '/updates/d' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y nginx-extras vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*