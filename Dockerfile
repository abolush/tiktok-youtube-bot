FROM python:3.12-slim

# ставим curl и прочее нужное
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# yt-dlp ставим через pip (без curl)
RUN pip install --no-cache-dir yt-dlp

COPY . .

CMD ["python", "main.py"]
