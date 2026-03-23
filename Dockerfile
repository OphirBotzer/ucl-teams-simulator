FROM python:3.14.2-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/* .

EXPOSE 8080
CMD ["python", "main.py"]