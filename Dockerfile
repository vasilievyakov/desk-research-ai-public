# Recipe the server uses to package the code. One image for every block:
# the block is chosen by the BLOCK variable (worker, bot, web, collector).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
# without BLOCK, main.py falls back to the Railway service name
CMD ["sh", "-c", "exec python main.py $BLOCK"]
