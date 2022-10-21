# hcl-playground

https://aripalo.com/blog/2020/aws-lambda-container-image-support/

docker build -t hcl-poc . && docker run -p 9000:8080 hcl-poc

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"payload":"locals {a=1}"}'