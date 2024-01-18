FROM python:3.10
ENV SECRET_KEY="mySecretKey"

WORKDIR /src
COPY requirements.txt .
COPY src .
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["flask","--app","app", "run", "--host=0.0.0.0", "--port=5001"]