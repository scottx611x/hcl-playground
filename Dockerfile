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

# Copy custom runtime bootstrap
COPY bootstrap ${LAMBDA_RUNTIME_DIR}
# Copy function code
COPY function.sh ${LAMBDA_TASK_ROOT}

COPY main.tf ${LAMBDA_TASK_ROOT}/main.tf

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "function.sh.handler" ]