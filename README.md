# hcl-playground
<img src="./app/static/dog.png" height=100px  alt="Cute dog with HCL on its collar"/>

### Testing locally
docker build -t flask-app . && docker run -v /tmp:/scratch -it -p 8080:8000 flask-app
http://localhost:8080