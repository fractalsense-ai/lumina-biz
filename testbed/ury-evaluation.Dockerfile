FROM frappe/erpnext:v16.60.0

ARG URY_REVISION=100c43fe2e52b21e41523c61e7fc1902baa96940

RUN git clone --branch version-16 --single-branch https://github.com/ury-erp/ury.git apps/ury \
    && git -C apps/ury checkout --detach "${URY_REVISION}" \
    && env/bin/pip install --no-deps -e apps/ury \
    && ln -s ../apps/ury/ury/public assets/ury

WORKDIR /home/frappe/frappe-bench/apps/ury
RUN yarn install --ignore-scripts --non-interactive \
    && yarn workspace pos build \
    && yarn workspace frontend build \
    && yarn --cwd mosaic install --non-interactive \
    && yarn --cwd mosaic build
WORKDIR /home/frappe/frappe-bench