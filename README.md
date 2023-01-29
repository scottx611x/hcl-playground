# hcl-playground

https://aripalo.com/blog/2020/aws-lambda-container-image-support/


### Testing locally
docker build -t 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:latest . && docker run -p 9000:8080 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:latest

curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -H 'content-type: application/json' -d '{"pathParameters": {"terraform_version": "1.3.3"}, "body": {"payload": "concat([1,2,3,4],[\"big\",\"yeet\",\"deer\",\"yam\"])"}}'

### Building and pushing to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 386710959426.dkr.ecr.us-east-1.amazonaws.com

docker build . -t 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:latest && docker push 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:latest

### Testing AWS Deployment
1. Build and push
2. Update Lambda image
3. curl -X POST "https://fc8i14k857.execute-api.us-east-1.amazonaws.com/development/1.3.3"   -H 'content-type: application/json' -d '{"payload": "setproduct([\"big\",\"yeet\"],[\"deer\",\"yam\"])"}'