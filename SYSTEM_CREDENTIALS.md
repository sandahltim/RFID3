# RFID3 System Credentials & Access Documentation
**CONFIDENTIAL - DO NOT COMMIT TO PUBLIC REPOS**
**Last Updated:** 2025-09-20
**Version:** 2.0.0-RFID-KVC

## 🔐 DATABASE CREDENTIALS

### Manager Database (rfid_inventory)
```bash
Host: localhost
Port: 3306
Database: rfid_inventory
Username: rfid_user
Password: rfid123!
Access: sudo mysql (for root access)
```

### Operations Database (rfid_operations_db)
```bash
Host: localhost
Port: 3306
Database: rfid_operations_db
Username: rfid_user
Password: rfid123!
Access: sudo mysql (for root access)
```

## 🌐 NETWORK ACCESS POINTS

### Executive/Manager Interface
```bash
Local: http://localhost:8101
Tailscale: https://100.103.67.41:8101
Service: rfid_dash_dev.service
Port: 6801 (internal Flask app)
```

### Operations API
```bash
Local: http://localhost:8444 (internal)
SSL/Tailscale: https://100.103.67.41:8443
Service: rfid_operations_api.service
Documentation: https://100.103.67.41:8443/docs
Health Check: https://100.103.67.41:8443/health
```

### Operations UI (To Be Implemented)
```bash
Planned Port: 443 (HTTPS)
Planned Access: https://100.103.67.41/
Service: rfid_operations_ui.service (planned)
```

## 📁 FILE LOCATIONS

### Application Directories
```bash
Manager App: /home/tim/RFID3/
Operations API: /home/tim/RFID3/operations_api/
Operations UI: /home/tim/RFID3/operations_ui/ (planned)
Virtual Environment: /home/tim/RFID3/venv/
```

### Configuration Files
```bash
Manager Config: /home/tim/RFID3/config.py
API Config: /home/tim/RFID3/operations_api/.env
API Alt Config: /home/tim/RFID3/rfid_operations_api/config/.env
Nginx Sites: /etc/nginx/sites-available/
```

### Service Files
```bash
Manager Service: /etc/systemd/system/rfid_dash_dev.service
API Service: /etc/systemd/system/rfid_operations_api.service
```

### SSL Certificates
```bash
Certificate: /etc/ssl/certs/nginx-selfsigned.crt
Key: /etc/ssl/private/nginx-selfsigned.key
Alt Certificate: /etc/ssl/certs/pi5-rfid3.crt
Alt Key: /etc/ssl/private/pi5-rfid3.key
```

## 🔑 API KEYS & TOKENS

### Operations API Security
```bash
SECRET_KEY: change-this-key-in-production (DEV ONLY)
Alt SECRET_KEY: rfid_ops_secret_key_change_in_production (DEV ONLY)
ALGORITHM: HS256
TOKEN_EXPIRE: 30 minutes
```

### External Services (If Configured)
```bash
RFIDpro API: Manual sync only (user-triggered)
POS System: CSV import via manager app
```

## 🚀 SERVICE COMMANDS

### System Services
```bash
# Manager/Executive Interface
sudo systemctl status rfid_dash_dev
sudo systemctl restart rfid_dash_dev
sudo journalctl -u rfid_dash_dev -f

# Operations API
sudo systemctl status rfid_operations_api
sudo systemctl restart rfid_operations_api
sudo journalctl -u rfid_operations_api -f

# Nginx
sudo systemctl status nginx
sudo systemctl reload nginx
sudo nginx -t
```

### Database Access
```bash
# Access as root
sudo mysql

# Access as rfid_user
mysql -u rfid_user -p'rfid123!'

# Select database
USE rfid_inventory;
USE rfid_operations_db;
```

## 🔄 SYNC & BACKUP

### Manual Database Sync
```bash
# Trigger sync from Manager to Operations DB
curl -X POST https://100.103.67.41:8443/api/v1/sync/manager \
  -H "Content-Type: application/json" \
  -d '{"source": "manager_db", "force": false}'
```

### Backup Commands
```bash
# Backup Manager Database
mysqldump -u rfid_user -p'rfid123!' rfid_inventory > backup_$(date +%Y%m%d).sql

# Backup Operations Database
mysqldump -u rfid_user -p'rfid123!' rfid_operations_db > ops_backup_$(date +%Y%m%d).sql
```

## 📊 MONITORING

### Log Files
```bash
Manager Logs: /home/tim/RFID3/logs/
API Logs: /home/tim/RFID3/logs/operations_api.log
Nginx Access: /var/log/nginx/access.log
Nginx Error: /var/log/nginx/error.log
```

### Health Checks
```bash
# Manager App Health
curl http://localhost:6801/health

# Operations API Health
curl -k https://localhost:8443/health
```

## ⚠️ SECURITY NOTES

1. **Change all default passwords in production**
2. **Generate new SECRET_KEYs for production**
3. **Replace self-signed certificates with proper SSL certs**
4. **Restrict database user permissions in production**
5. **Enable firewall rules for production deployment**
6. **Regular backup schedule should be implemented**

## 📝 VERSION HISTORY

- **v2.0.0-RFID-KVC** (2025-09-20): API-first architecture with Operations API
- **v1.5.0** (2025-09-17): Phase 2.5 completion with POS integration
- **v1.0.0** (2025-08-30): Initial system deployment

## 🆘 TROUBLESHOOTING

### Common Issues
```bash
# 502 Bad Gateway: Check if services are running
sudo systemctl status rfid_operations_api

# Database connection issues
sudo mysql -e "SHOW GRANTS FOR 'rfid_user'@'localhost';"

# Port conflicts
sudo netstat -tlnp | grep -E "8101|8443|6801|8444"
```

---
**Remember:** Keep this file secure and never commit to public repositories!