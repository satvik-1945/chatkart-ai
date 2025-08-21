FROM python:3.10-slim

# Install system dependencies + cloudflared
RUN apt-get update && apt-get install -y curl && \
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# Copy app files
WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5007

# Start both Flask app and Cloudflared tunnel
CMD cloudflared tunnel --url http://localhost:5007 --no-autoupdate &
CMD ["python", "app.py"]