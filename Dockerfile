FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8010

# Launch uvicorn directly so --host 0.0.0.0 is respected.
# Running `python api_fastapi.py` hits the __main__ block which
# hardcodes host="127.0.0.1", making the container unreachable.
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "8010"]