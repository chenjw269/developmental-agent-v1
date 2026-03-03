# 基于官方 apache/apisix-docker debian 构建，使用 AWS ECR 基础镜像避免 Docker Hub
# 来源: https://github.com/apache/apisix-docker/blob/master/debian/Dockerfile
FROM public.ecr.aws/docker/library/debian:bullseye-slim

ARG APISIX_VERSION=3.11.0

RUN set -ex; \
    arch=$(dpkg --print-architecture); \
    apt update; \
    apt-get -y install --no-install-recommends wget gnupg ca-certificates curl; \
    codename=`grep -Po 'VERSION="[0-9]+ \(\K[^)]+' /etc/os-release`; \
    case "${arch}" in \
        amd64) \
            wget -O - https://repos.apiseven.com/pubkey.gpg | apt-key add - \
            && echo "deb https://repos.apiseven.com/packages/debian $codename main" | tee /etc/apt/sources.list.d/apisix.list \
            ;; \
        arm64) \
            wget -O - https://repos.apiseven.com/pubkey.gpg | apt-key add - \
            && echo "deb https://repos.apiseven.com/packages/arm64/debian $codename main" | tee /etc/apt/sources.list.d/apisix.list \
            ;; \
    esac; \
    apt update \
    && apt install -y apisix=${APISIX_VERSION}-0 \
    && apt-get purge -y --auto-remove \
    && rm -f /usr/local/openresty/bin/etcdctl \
    && openresty -V \
    && apisix version

COPY ./install-brotli.sh /install-brotli.sh
RUN chmod +x /install-brotli.sh \
    && cd / && ./install-brotli.sh && rm -rf /install-brotli.sh

RUN apt-get -y purge --auto-remove curl wget gnupg --allow-remove-essential

# healthcheck 需要 curl
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/apisix

ENV PATH=$PATH:/usr/local/openresty/luajit/bin:/usr/local/openresty/nginx/sbin:/usr/local/openresty/bin

RUN groupadd --system --gid 636 apisix \
    && useradd --system --gid apisix --no-create-home --shell /usr/sbin/nologin --uid 636 apisix \
    && chown -R apisix:apisix /usr/local/apisix

USER apisix

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /usr/local/apisix/logs/access.log \
    && ln -sf /dev/stderr /usr/local/apisix/logs/error.log

EXPOSE 9080 9443 9180

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY ./check_standalone_config.sh /check_standalone_config.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["docker-start"]

STOPSIGNAL SIGQUIT
