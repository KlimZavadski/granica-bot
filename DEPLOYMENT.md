# Deployment Guide

## Option 1: Deploy to is_hosting

### Prerequisites
- is_hosting account
- Domain (optional)

### Steps

1. **Prepare the project**
```bash
# Ensure all dependencies are in requirements.txt
pip freeze > requirements.txt
```

2. **Create Procfile**
```
worker: python bot.py
```

3. **Push to is_hosting**
```bash
# Follow is_hosting specific deployment instructions
# Usually involves git push or their CLI tool
```

4. **Set environment variables**
In is_hosting dashboard, set:
- `TELEGRAM_BOT_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ENVIRONMENT=production`

---

## Option 2: Deploy to VPS (Ubuntu/Debian)

### Prerequisites
- Ubuntu 20.04+ or Debian 11+ VPS
- SSH access
- Domain (optional)

### Steps

1. **Connect to VPS**
```bash
ssh user@your-vps-ip
```

2. **Install dependencies**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

3. **Clone repository**
```bash
cd /opt
sudo git clone <your-repo-url> granica-bot
cd granica-bot
```

4. **Setup environment**
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

5. **Configure environment**
```bash
sudo nano .env
# Add your credentials
```

6. **Create systemd service**
```bash
sudo nano /etc/systemd/system/granica-bot.service
```

Add:
```ini
[Unit]
Description=Granica Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/granica-bot
Environment="PATH=/opt/granica-bot/venv/bin"
ExecStart=/opt/granica-bot/venv/bin/python3 /opt/granica-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

7. **Start the service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable granica-bot
sudo systemctl start granica-bot
```

8. **Check status**
```bash
sudo systemctl status granica-bot
sudo journalctl -u granica-bot -f  # View logs
```

---

## Option 3: Deploy with Docker

### Prerequisites
- Docker installed
- docker-compose installed

### Steps

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "bot.py"]
```

2. **Create docker-compose.yml**
```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file:
      - .env
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

3. **Run**
```bash
docker-compose up -d
```

4. **View logs**
```bash
docker-compose logs -f
```

---

## Monitoring & Maintenance

### Check bot is running
```bash
# If using systemd
sudo systemctl status granica-bot

# If using Docker
docker-compose ps
```

### View logs
```bash
# Systemd
sudo journalctl -u granica-bot -f

# Docker
docker-compose logs -f
```

### Update bot
```bash
# Pull latest code
git pull

# Restart service
sudo systemctl restart granica-bot

# Or with Docker
docker-compose restart
```

### Database backup
Supabase handles backups automatically. To export manually:
1. Go to Supabase Dashboard
2. Database → Backups
3. Export SQL dump

---

## Troubleshooting

### Bot not responding
1. Check if service is running
2. Check logs for errors
3. Verify environment variables
4. Test Telegram API connection: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### Database connection issues
1. Verify Supabase credentials
2. Check network connectivity
3. Ensure Supabase project is active
4. Check IP allowlist in Supabase settings

### Memory issues
If bot uses too much memory:
1. Restart service regularly (cron job)
2. Monitor with `htop`
3. Consider upgrading VPS

---

## Security Best Practices

1. **Never commit .env file**
2. **Use environment variables for secrets**
3. **Keep dependencies updated**: `pip list --outdated`
4. **Use HTTPS for webhooks** (if switching from polling)
5. **Regular backups** of database
6. **Monitor logs** for suspicious activity
7. **Rate limiting** - aiogram has built-in protection

---

## Production Checklist

- [ ] Environment variables set correctly
- [ ] Database schema applied
- [ ] Bot token works (@BotFather)
- [ ] Supabase connection works
- [ ] Service auto-starts on reboot
- [ ] Logs are being written
- [ ] Monitoring in place
- [ ] Backup strategy defined
- [ ] SSL/TLS enabled (if using webhooks)
- [ ] Error notifications configured

---

## Scaling Considerations

### When to scale:
- More than 10,000 active users
- Message processing delays
- Database query timeouts

### Options:
1. **Horizontal scaling**: Multiple bot instances (webhook mode required)
2. **Database optimization**: Add indexes, use connection pooling
3. **Caching**: Redis for FSM state (instead of MemoryStorage)
4. **Queue system**: Celery for background tasks
5. **CDN**: For static content (graphs, images)

---

## Support

For deployment issues, check:
- README.md for basic setup
- GitHub Issues for known problems
- Telegram Bot API documentation

