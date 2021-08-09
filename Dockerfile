FROM python:3.9-alpine as base
FROM base as builder

RUN apk add --no-cache --virtual .build-deps make g++

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install --no-binary multidict,yarl -r /requirements.txt

ONBUILD RUN apk del .build-deps

FROM base

COPY --from=builder /install /usr/local

# Google authentication stuff
ARG google_service_account
ARG google_private_key_json

COPY ./demo1/api /app/demo1/api
COPY ./amouse /app/amouse
COPY demo1.flutter /app
COPY pr1.flutter /app
COPY google_token.pickle /app
COPY .prebuild/.demo1 /root/.demo1
WORKDIR /app

# RUN ls -la /app
RUN ls -la /usr/local/lib/python3.9/site-packages

ENV PYTHONPATH "${PYTHONPATH}:/usr/local/lib/python3.9/site-packages:/app"
ENV GOOGLE_SERVICE_ACCOUNT=${google_service_account}
ENV GOOGLE_PRIVATE_KEY_JSON=${google_private_key_json}

EXPOSE 443
CMD python3 -m demo1.api.demo1 -p 443 -k /root/.demo1 -a 0.0.0.0 -g1 "${GOOGLE_SERVICE_ACCOUNT}" -g2 "${GOOGLE_PRIVATE_KEY_JSON}"
