FROM python:3.10.1-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirments.txt

COPY /app .

CMD ["python", "-m flask run --port 80"]
