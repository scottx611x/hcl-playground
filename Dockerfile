FROM python:3.12.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pre-bake pinned Terraform versions via tfenv (no per-request installs). The set
# of installed versions IS the runtime allowlist (see backend.terraform_utils).
ARG TF_VERSIONS="1.9.8 1.8.5 1.7.5"
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /opt/tfenv \
    && for v in $TF_VERSIONS; do TFENV_ROOT=/opt/tfenv /opt/tfenv/bin/tfenv install "$v"; done

# Pre-bake pinned OpenTofu versions via tofuenv.
ARG TOFU_VERSIONS="1.8.5 1.7.3 1.6.3"
RUN git clone --depth=1 https://github.com/tofuutils/tofuenv.git /opt/tofuenv \
    && for v in $TOFU_VERSIONS; do TOFUENV_ROOT=/opt/tofuenv /opt/tofuenv/bin/tofuenv install "$v"; done

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-dev.txt .
ARG INSTALL_DEV_DEPS=false
RUN if [ "$INSTALL_DEV_DEPS" = "true" ] ; then pip install --no-cache-dir -r requirements-dev.txt ; fi
RUN rm requirements-dev.txt

COPY tests tests
RUN if [ "$INSTALL_DEV_DEPS" = "false" ] ; then rm -r tests; fi

COPY app/ /app

# Non-root user; own /scratch so the app can write even without a volume mount.
RUN adduser --disabled-password --gecos '' app-user \
    && mkdir -p /scratch \
    && chown app-user:app-user /scratch
USER app-user

EXPOSE 8080

VOLUME ["/scratch"]

CMD ["uwsgi", "--ini", "uwsgi.ini"]
