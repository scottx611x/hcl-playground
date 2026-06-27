FROM python:3.12.2

# Lambda Web Adapter — only activates under the Lambda runtime; ignored by a
# plain `docker run`, so the same image runs locally and on Lambda.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pre-bake pinned Terraform versions via tfenv (no per-request installs). The set
# of installed versions IS the runtime allowlist (see backend.terraform_utils).
# A small default set keeps the image lean; more can be installed on demand
# locally, and overridden via build args.
ARG TF_VERSIONS="1.10.5 1.9.8"
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /opt/tfenv \
    && for v in $TF_VERSIONS; do TFENV_ROOT=/opt/tfenv /opt/tfenv/bin/tfenv install "$v"; done

# Pre-bake pinned OpenTofu versions via tofuenv.
ARG TOFU_VERSIONS="1.10.10 1.8.11"
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

# Non-root user; own /scratch (work area) and the engine roots so versions can be
# installed on demand at runtime (in the default run; the hardened read-only run
# is frozen to the pre-baked set).
RUN adduser --disabled-password --gecos '' app-user \
    && mkdir -p /scratch \
    && chown app-user:app-user /scratch \
    && chown -R app-user:app-user /opt/tfenv /opt/tofuenv
USER app-user

EXPOSE 8080

# /scratch is an ephemeral per-request work area; no external volume needed.
# (For a hardened run with --read-only, mount a tmpfs there — see the README.)

CMD ["uwsgi", "--ini", "uwsgi.ini"]
