FROM public.ecr.aws/lambda/provided:al2

RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
RUN yum -y install jq git-all unzip

# Install tfenv
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /home/root/.tfenv
RUN ln -s /home/root/.tfenv/bin/* /usr/local/bin

# Sad hack to avoid errors like the following in the Lambda execution environment:
# `/usr/bin/sha256sum: /dev/fd/63: No such file or directory`
# ref: https://github.com/aws/aws-sam-cli/issues/622
# ref: https://github.com/tfutils/tfenv/blob/34c744b2c6722738a7586e14cd5cfafef94a3a72/libexec/tfenv-install#L291
RUN rm /usr/bin/shasum
RUN rm /usr/bin/sha256sum

# Install dependencies required for building Python
RUN yum groupinstall -y "Development Tools" && \
    yum install -y \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    xz-devel \
    tk-devel \
    gdbm-devel \
    ncurses-devel \
    sqlite-devel \
    readline-devel \
    db4-devel \
    libpcap-devel \
    xz-libs \
    wget \
    tar

# Download Python 3.12 source code
RUN wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz

# Extract the source code tarball
RUN tar xzf Python-3.12.0.tgz

# Configure and build Python from source
RUN cd Python-3.12.0 && \
    ./configure --enable-optimizations && \
    make altinstall

# Clean up cache and source files to reduce image size
RUN rm -rf Python-3.12.0.tgz Python-3.12.0 && \
    yum clean all

# Remove existing python3 link and create a new symbolic link to Python 3.12
RUN rm -f /usr/bin/python3 && \
    ln -s /usr/local/bin/python3.12 /usr/bin/python3

# Verify Python installation
RUN python3 --version

# Copy custom runtime bootstrap
COPY bootstrap ${LAMBDA_RUNTIME_DIR}
# Copy function code
COPY function.py ${LAMBDA_TASK_ROOT}

COPY main.tf ${LAMBDA_TASK_ROOT}/main.tf

CMD [ "function.py" ]