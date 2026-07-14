FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY src ./src
COPY models ./models

ENV PORT=7861
EXPOSE 7861

CMD ["python", "-m", "src.app"]
