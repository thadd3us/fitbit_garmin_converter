FROM python:3.11-slim@sha256:1d6131b5d479888b43200645e03a78443c7157efbdb730e6b48129740727c312
# Needed for Alpine:
# RUN apk add --no-cache python3 py3-pip bash
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"

RUN pip install --no-cache-dir uv
# RUN pip install --no-cache-dir numpy
# RUN python -c "import numpy"
RUN which uv

WORKDIR /tmp/uv_warmup
COPY pyproject.toml uv.lock /tmp/uv_warmup/
RUN uv sync --all-groups --active
RUN python -c "import numpy"

RUN chmod a+rwX -R /venv

WORKDIR /
CMD ["bash"]
