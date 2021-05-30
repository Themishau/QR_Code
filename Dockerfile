# Dockerfile, Image, Container
FROM python:3.9

WORKDIR /

COPY requirements.txt .
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python
RUN apt-get update && \
    apt-get install -y build-essential libzbar-dev
RUN pip install -r requirements.txt


COPY / .

CMD ["python", "main.py"]

