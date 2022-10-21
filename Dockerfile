FROM public.ecr.aws/lambda/provided:al2

RUN yum install -y yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
RUN yum -y install terraform jq
RUN terraform --version

# Copy custom runtime bootstrap
COPY bootstrap ${LAMBDA_RUNTIME_DIR}
# Copy function code
COPY function.sh ${LAMBDA_TASK_ROOT}

COPY main.tf ${LAMBDA_TASK_ROOT}/main.tf

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "function.sh.handler" ]