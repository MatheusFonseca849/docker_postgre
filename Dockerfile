FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl.py dashboard.py ./
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/
COPY start.sh .
RUN chmod +x start.sh

CMD ["bash", "start.sh"]
