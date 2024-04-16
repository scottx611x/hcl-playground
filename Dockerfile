FROM python:3.12.2

# Install tfenv
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git /home/root/.tfenv
RUN ln -s /home/root/.tfenv/bin/* /usr/local/bin

WORKDIR app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY requirements-dev.txt .
ARG INSTALL_DEV_DEPS=false
RUN if [ "$INSTALL_DEV_DEPS" = "true" ] ; then pip install -r requirements-dev.txt ; fi
RUN rm requirements-dev.txt

COPY tests tests
RUN if [ "$INSTALL_DEV_DEPS" = "false" ] ; then rm -r tests; fi


COPY app/ /app

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' app-user
USER app-user

EXPOSE 8080

# TODO: this will be an external volume mount in prod
VOLUME ["/scratch"]

CMD ["uwsgi", "--ini", "uwsgi.ini"]