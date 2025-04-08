FROM python:3.9-slim

WORKDIR /app

COPY frontend/ /app/frontend/
COPY backend/ /app/backend/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install pymongo

EXPOSE 8000
EXPOSE 5000

CMD ["sh", "-c", "cd /app/backend && python main.py & wait $(jobs -p) && cd /app/frontend && python main.py"]
