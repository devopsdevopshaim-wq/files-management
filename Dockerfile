FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# הגדרות nginx
COPY nginx.conf /etc/nginx/nginx.conf

# הגדרות supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# יצירת תיקיות
RUN mkdir -p /app/uploads /app/logs /var/log/supervisor

# הרשאות
RUN chmod +x /app/start.sh

EXPOSE 80 5000 8080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]