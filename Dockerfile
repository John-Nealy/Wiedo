FROM python:3.10.1-buster

WORKDIR /app

COPY requirments.txt .
RUN pip install -r requirments.txt

COPY / .

CMD ["python", "app.py"]
