FROM python:3.12

# Install tfenv
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /home/root/.tfenv
RUN ln -s /home/root/.tfenv/bin/* /usr/local/bin

WORKDIR app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ /app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]