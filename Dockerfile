FROM alpine:3.22.1@sha256:4bcff63911fcb4448bd4fdacec207030997caf25e9bea4045fa6c8c44de311d1
# RUN pip install --no-cache-dir uv
# RUN which uv
RUN echo "Hello Imbue!" > /hello_sculptor.txt
