# 🚀 Neuronaut World - Deployment Guide

## How to Deploy to Production

This guide shows you how to deploy Neuronaut World to a cloud server so anyone can access it.

## Deployment Options

### Option 1: DigitalOcean (Recommended for Start)

**Cost:** $12-24/month
**Best for:** Getting started quickly

### Option 2: AWS/GCP

**Cost:** $20-100+/month
**Best for:** Scaling to large audiences

### Option 3: Heroku

**Cost:** $25+/month
**Best for:** Easiest deployment

## Quick Deploy (DigitalOcean)

### Step 1: Create Droplet

1. Go to https://digitalocean.com
2. Create account / Sign in
3. Click "Create" → "Droplets"
4. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic $12/month (2GB RAM)
   - **Region:** Closest to your users
   - **Authentication:** SSH key (create if needed)
5. Create Droplet

### Step 2: SSH Into Server

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.10+
apt install python3.10 python3.10-venv python3-pip -y

# Install nginx
apt install nginx -y

# Install certbot (for SSL)
apt install certbot python3-certbot-nginx -y
```

### Step 4: Deploy Application

```bash
# Clone your repository (or upload files)
cd /opt
git clone https://github.com/yourusername/neuronaut-world.git
cd neuronaut-world

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test run
python main.py
# Ctrl+C to stop
```

### Step 5: Set Up as System Service

Create service file:

```bash
nano /etc/systemd/system/neuronaut.service
```

Add:

```ini
[Unit]
Description=Neuronaut World
After=network.target

[Service]
User=root
WorkingDirectory=/opt/neuronaut-world
Environment="PATH=/opt/neuronaut-world/venv/bin"
ExecStart=/opt/neuronaut-world/venv/bin/python main.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl enable neuronaut
systemctl start neuronaut
systemctl status neuronaut  # Check it's running
```

### Step 6: Configure Nginx

```bash
nano /etc/nginx/sites-available/neuronaut
```

Add:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;  # Or use IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

Enable site:

```bash
ln -s /etc/nginx/sites-available/neuronaut /etc/nginx/sites-enabled/
nginx -t  # Test configuration
systemctl restart nginx
```

### Step 7: Add SSL (HTTPS)

```bash
certbot --nginx -d YOUR_DOMAIN.com
```

Follow prompts. Certbot will automatically update nginx config for HTTPS.

### Step 8: Open Firewall

```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw enable
```

## You're Live!

Visit **https://YOUR_DOMAIN.com/app**

The world is now running 24/7!

## Monitoring & Maintenance

### Check Logs

```bash
# Application logs
journalctl -u neuronaut -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Restart Service

```bash
systemctl restart neuronaut
```

### Update Code

```bash
cd /opt/neuronaut-world
git pull
systemctl restart neuronaut
```

### Monitor Resources

```bash
htop  # Install: apt install htop
```

## Scaling Up

### When to Scale

Signs you need more resources:
- CPU usage consistently >80%
- Memory usage >90%
- Slow response times
- 500+ concurrent viewers

### Vertical Scaling (Bigger Server)

DigitalOcean:
1. Go to Droplet
2. Click "Resize"
3. Choose bigger plan (4GB, 8GB, etc.)
4. Resize and reboot

### Horizontal Scaling (Multiple Servers)

For 1,000+ concurrent users:

1. **Load Balancer** (distribute traffic)
2. **Database Server** (shared state)
3. **Redis** (caching, real-time sync)
4. **Multiple App Servers**

Architecture:
```
Load Balancer
    ↓
App Server 1 ──┐
App Server 2 ──┼─→ Shared Database
App Server 3 ──┘      Redis Cache
```

## Performance Optimization

### 1. Database

Switch from in-memory to PostgreSQL:

```bash
apt install postgresql postgresql-contrib
pip install psycopg2-binary sqlalchemy
```

Update database connection in code.

### 2. Caching

Add Redis:

```bash
apt install redis-server
pip install redis aioredis
```

Cache world state for faster API responses.

### 3. CDN

Use Cloudflare (free) for:
- Static file caching
- DDoS protection
- Global CDN

Setup:
1. Point domain to Cloudflare
2. Enable proxy
3. Configure caching rules

### 4. Optimize Simulation

```python
# Reduce tick rate for large populations
simulation.tick_rate = 2.0  # Slower but less CPU

# Limit agent perception range
perception_range = 5.0  # Instead of 10.0

# Optimize world size
world_width = 50  # Instead of 100
```

## Backup & Recovery

### Automatic Backups

```bash
# Backup script
nano /opt/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup world state (if using files)
tar -czf $BACKUP_DIR/neuronaut_$DATE.tar.gz /opt/neuronaut-world/data

# Keep only last 7 days
find $BACKUP_DIR -name "neuronaut_*.tar.gz" -mtime +7 -delete
```

Make executable:

```bash
chmod +x /opt/backup.sh
```

Add to cron:

```bash
crontab -e
```

Add:

```
0 2 * * * /opt/backup.sh
```

### Restore from Backup

```bash
cd /opt/neuronaut-world
tar -xzf /opt/backups/neuronaut_YYYYMMDD_HHMMSS.tar.gz
systemctl restart neuronaut
```

## Security

### 1. Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

### 2. Fail2Ban (Block Attackers)

```bash
apt install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### 3. Regular Updates

```bash
apt update && apt upgrade -y
```

Set up automatic updates:

```bash
apt install unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Environment Variables

Never commit secrets! Use environment variables:

```bash
nano /opt/neuronaut-world/.env
```

```
STRIPE_SECRET_KEY=sk_live_...
DATABASE_URL=postgresql://...
FIREBASE_KEY=...
```

Update systemd service to load .env:

```ini
[Service]
EnvironmentFile=/opt/neuronaut-world/.env
```

## Cost Optimization

### DigitalOcean

- **Start:** $12/month (2GB droplet)
- **Growth:** $24/month (4GB droplet)
- **Scale:** $48-96/month (8-16GB droplet)

### AWS Free Tier

- t2.micro free for 1 year
- Enough for testing/small audience
- Upgrade as needed

### Cost Breakdown

For 10,000 users:
- **Server:** $96/month (16GB droplet)
- **Database:** $15/month (managed PostgreSQL)
- **CDN:** $0-20/month (Cloudflare free/pro)
- **Backups:** $5/month
- **Total:** ~$120/month

**Revenue at 1% conversion to $15/month premium:**
- 10,000 users × 1% × $15 = $1,500/month
- Profit: $1,380/month

## Monitoring Tools

### Free

- **UptimeRobot** - Monitor uptime
- **Google Analytics** - Track usage
- **Sentry** - Error tracking

### Paid

- **DataDog** - Full monitoring
- **New Relic** - Performance
- **LogDNA** - Log management

## Troubleshooting

### Service Won't Start

```bash
journalctl -u neuronaut -n 50
```

Common issues:
- Python version mismatch
- Missing dependencies
- Port already in use
- Permission errors

### Out of Memory

```bash
free -h  # Check memory
```

Solutions:
- Reduce agent count
- Increase droplet size
- Add swap space

### Slow Performance

```bash
htop  # Check CPU/memory
```

Solutions:
- Optimize code
- Reduce tick rate
- Add caching
- Scale vertically

## Docker Deployment (Alternative)

Create `Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t neuronaut-world .
docker run -p 8000:8000 neuronaut-world
```

Deploy with Docker Compose:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    restart: always
    environment:
      - DATABASE_URL=postgresql://...
```

## Production Checklist

Before going live:

- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Automatic backups enabled
- [ ] Monitoring set up
- [ ] Error logging configured
- [ ] Environment variables secured
- [ ] Database backed up
- [ ] Load tested
- [ ] Domain configured
- [ ] Analytics installed

## Support & Maintenance

### Daily

- Check logs for errors
- Monitor uptime
- Check resource usage

### Weekly

- Review analytics
- Check backups
- Update dependencies

### Monthly

- Security updates
- Performance optimization
- Feature releases
- Cost review

## Next Steps

1. Deploy to production
2. Test thoroughly
3. Launch to public
4. Monitor performance
5. Iterate based on feedback
6. Scale as needed

**You're ready to launch Neuronaut World to the world!**

---

Need help? Check logs, search GitHub issues, or reach out to the community.

🚀 **Now deploy and let the world watch AI create civilization!**
