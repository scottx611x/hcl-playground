FROM public.ecr.aws/lambda/provided:al2

RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
RUN yum -y install jq git-all unzip

# Install tfenv and a bunch of terraform versions
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /home/root/.tfenv
RUN ln -s /home/root/.tfenv/bin/* /usr/local/bin
RUN tfenv install latest
RUN tfenv install latest:^1.3
RUN tfenv install latest:^1.2
RUN tfenv install latest:^1.1
RUN tfenv install latest:^1.0


# Copy custom runtime bootstrap
COPY bootstrap ${LAMBDA_RUNTIME_DIR}
# Copy function code
COPY function.sh ${LAMBDA_TASK_ROOT}

COPY main.tf ${LAMBDA_TASK_ROOT}/main.tf

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "function.sh.handler" ]