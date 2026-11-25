FROM frappe/erpnext:v16.60.0

ARG LUMEN_REVISION=083820186e282e76add31d3c30fd0e62ca35cd32

RUN git clone https://github.com/abdullla00/LumenRestaurants.git apps/lumen_restaurants \
    && git -C apps/lumen_restaurants checkout --detach "${LUMEN_REVISION}" \
    && env/bin/pip install --no-deps -e apps/lumen_restaurants \
    && ln -s ../apps/lumen_restaurants/lumen_restaurants/public assets/lumen_restaurants