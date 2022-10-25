# hcl-playground

https://aripalo.com/blog/2020/aws-lambda-container-image-support/


### Testing locally
docker build -t 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:poc . && docker run -p 9000:8080 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:poc
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations"   -H 'content-type: application/json' -d '{"body": {"payload": "concat([1,2,3,4],[\"big\",\"yeet\",\"deer\",\"yam\"])"}}'


### Building and pushing to ECR
docker build . -t 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:poc && docker push 386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:poc

### Testing AWS Deployment
1. Build and push
2. Update Lambda image
3. curl -X POST "https://9wefmhwci7.execute-api.us-east-1.amazonaws.com/default/hcl-playground-poc"   -H 'content-type: application/json' -d '{"payload": "setproduct([\"big\",\"yeet\"],[\"deer\",\"yam\"])"}'