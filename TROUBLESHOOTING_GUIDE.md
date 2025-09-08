# RFID3 Troubleshooting Guide

**Version:** 3.0  
**Last Updated:** September 1, 2025  
**Scope:** Performance Issues, System Errors, Data Problems, Configuration Issues

---

## 📋 Quick Diagnosis Checklist

### System Health Check (First Step)
```bash
# Run comprehensive health check
curl http://localhost:6800/health

# Check system status
systemctl status rfid3

# Verify service logs
sudo journalctl -u rfid3 -n 50 --no-pager
```

### Performance Quick Check
```bash
# Test Tab 2 performance
curl http://localhost:6800/tab/2/performance_stats

# Test API response times
time curl http://localhost:6800/api/inventory/dashboard_summary

# Check database connectivity
mysql -u rfid_user -p -e "SELECT COUNT(*) FROM id_item_master;" rfid_inventory
```

---

## ⚡ Performance Issues

### Tab 2 Slow Loading (Previously 5-30 seconds)

#### Expected Performance After Optimization:
- **Target**: 0.5-2 seconds load time
- **Query Count**: 1 single optimized query (was 300+)
- **Memory Usage**: 90% reduction through pagination

#### Diagnosis Steps:
```bash
# 1. Check performance statistics
curl http://localhost:6800/tab/2/performance_stats
# Expected: queries_reduced_percentage > 90%, cache_hit_rate > 60%

# 2. Verify cache status
redis-cli info memory
redis-cli info stats

# 3. Check database indexes
mysql -u rfid_user -p rfid_inventory << 'SQL'
SHOW INDEX FROM id_item_master WHERE Key_name LIKE 'ix_%';
SHOW INDEX FROM id_transactions WHERE Key_name LIKE 'ix_%';
SQL

# 4. Monitor query performance
mysql -u rfid_user -p rfid_inventory << 'SQL'
SHOW PROCESSLIST;
SELECT * FROM information_schema.processlist WHERE TIME > 1;
SQL
```

#### Common Solutions:

**Problem**: Tab 2 still loading slowly after optimization
```bash
# Solution 1: Clear cache and restart
curl -X POST http://localhost:6800/tab/2/cache_clear
sudo systemctl restart rfid3

# Solution 2: Check for missing indexes
mysql -u rfid_user -p rfid_inventory < database_performance_optimization.sql

# Solution 3: Verify pagination is working
curl "http://localhost:6800/tab/2?page=1&per_page=20"
# Should return paginated results with performance metrics
```

**Problem**: High memory usage despite pagination
```bash
# Check application memory usage
ps aux | grep python | grep rfid3
free -h

# Solution: Restart application and check for memory leaks
sudo systemctl restart rfid3
# Monitor memory usage over time
watch -n 5 'free -h && ps aux | grep python | grep rfid3'
```

**Problem**: Cache not improving performance
```bash
# Check Redis status
redis-cli info stats | grep hit
redis-cli info memory

# Solution: Verify cache configuration
grep -r "CACHE_TYPE" /opt/rfid3/app/config.py
grep -r "cache.cached" /opt/rfid3/app/app/routes/tab2.py
```

### API Response Time Issues

#### Expected Performance:
- **API Average**: 0.1-0.5 seconds
- **Database Queries**: <0.05 seconds average
- **Cache Hit Rate**: 60-90%

#### Diagnosis Commands:
```bash
# Test specific API endpoints
time curl http://localhost:6800/api/inventory/dashboard_summary
time curl http://localhost:6800/bi/dashboard
time curl http://localhost:6800/api/financial/store-performance

# Check database performance
mysql -u rfid_user -p rfid_inventory << 'SQL'
SHOW STATUS LIKE 'Slow_queries';
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Questions';
SQL
```

#### Solutions:

**Problem**: API responses taking >2 seconds
```bash
# Solution 1: Check connection pool status
grep -A 10 "SQLALCHEMY_ENGINE_OPTIONS" /opt/rfid3/app/config.py
# Should show: pool_size=15, max_overflow=25

# Solution 2: Optimize database connections
mysql -u root -p << 'SQL'
SHOW STATUS LIKE 'Max_used_connections';
SHOW STATUS LIKE 'Threads_connected';
SHOW VARIABLES LIKE 'max_connections';
SQL

# Solution 3: Clear all caches
redis-cli FLUSHALL
sudo systemctl restart rfid3
```

---

## 🗄️ Database Issues

### Connection Problems

#### Symptoms:
- "Can't connect to MySQL server"
- "Too many connections"
- "Lost connection to MySQL server"

#### Diagnosis:
```bash
# Check database status
sudo systemctl status mariadb
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Check connection configuration
mysql -u root -p << 'SQL'
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Max_used_connections';
SHOW STATUS LIKE 'Connection_errors%';
SQL
```

#### Solutions:

**Problem**: "Too many connections" error
```bash
# Immediate fix: Kill long-running queries
mysql -u root -p << 'SQL'
SHOW PROCESSLIST;
-- Kill specific problematic queries
-- KILL [process_id];
SQL

# Permanent fix: Increase connection limits
sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf
# Add or modify:
# max_connections = 200
# wait_timeout = 600
# interactive_timeout = 600

sudo systemctl restart mariadb
```

**Problem**: Connection pool exhaustion
```bash
# Check application connection pool
grep -A 5 "pool_size" /opt/rfid3/app/config.py

# Monitor connections over time
watch -n 2 'mysql -u root -p -e "SHOW STATUS LIKE \"Threads_connected\";"'

# Solution: Restart application
sudo systemctl restart rfid3
```

### Data Quality Issues

#### Store Marker Attribution Problems

#### Symptoms:
- Missing store data in reports
- Incorrect store assignment in CSV imports
- Company-wide (000) data not aggregating properly

#### Diagnosis:
```bash
# Check store marker validation
curl http://localhost:6800/api/csv/store-markers

# Verify store attribution in database
mysql -u rfid_user -p rfid_inventory << 'SQL'
SELECT store_code, COUNT(*) 
FROM scorecard_trends 
GROUP BY store_code 
ORDER BY store_code;

SELECT store_attribution, COUNT(*) 
FROM pl_data 
GROUP BY store_attribution;
SQL
```

#### Solutions:

**Problem**: CSV imports not attributing store markers correctly
```bash
# Solution 1: Check CSV processing logs
tail -f /opt/rfid3/logs/csv_processing.log

# Solution 2: Validate CSV file formats
python3 << 'PYTHON'
import pandas as pd
import glob

csv_files = glob.glob('/opt/rfid3/app/shared/POR/*.csv')
for file in csv_files:
    try:
        df = pd.read_csv(file, nrows=5)
        print(f"\n{file} columns:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Error reading {file}: {e}")
PYTHON

# Solution 3: Re-run CSV processing
python3 -c "
import sys
sys.path.append('/opt/rfid3/app')
from app.services.csv_import_service import CSVImportService
service = CSVImportService()
result = service.process_all_csv_files()
print(f'Processing result: {result}')
"
```

**Problem**: Financial data not correlating with operational data
```bash
# Check data correlation status
curl http://localhost:6800/api/system/metrics

# Verify data relationships
mysql -u rfid_user -p rfid_inventory << 'SQL'
-- Check P&L to scorecard correlation
SELECT 
    p.store_attribution, 
    s.store_code,
    COUNT(*) as correlation_count
FROM pl_data p
LEFT JOIN scorecard_trends s ON p.store_attribution = s.store_code
GROUP BY p.store_attribution, s.store_code;
SQL

# Solution: Run correlation analysis
python comprehensive_database_correlation_analyzer.py
```

---

## 💾 Cache Issues

### Redis Problems

#### Symptoms:
- Cache hit rates below 50%
- "Connection refused" Redis errors
- Memory usage growing continuously

#### Diagnosis:
```bash
# Check Redis status
redis-cli ping
redis-cli info memory
redis-cli info stats | grep -E "(hit|miss)"

# Check Redis configuration
cat /etc/redis/redis.conf | grep -E "(maxmemory|save)"
```

#### Solutions:

**Problem**: Redis connection errors
```bash
# Check Redis service
sudo systemctl status redis-server
sudo systemctl restart redis-server

# Verify Redis configuration
redis-cli config get maxmemory
redis-cli config get maxmemory-policy

# Test connectivity
redis-cli set test "hello"
redis-cli get test
redis-cli del test
```

**Problem**: Low cache hit rates (<50%)
```bash
# Check cache configuration in application
grep -r "cache.cached" /opt/rfid3/app/app/routes/
grep -A 5 "CACHE_CONFIG" /opt/rfid3/app/config.py

# Clear and warm cache
curl -X POST http://localhost:6800/tab/2/cache_clear
curl http://localhost:6800/tab/2  # Warm cache
curl http://localhost:6800/tab/2  # Should be faster (cache hit)
```

**Problem**: Redis memory issues
```bash
# Check memory usage
redis-cli info memory

# Set memory policy if not configured
redis-cli config set maxmemory 1gb
redis-cli config set maxmemory-policy allkeys-lru

# Clear unnecessary keys
redis-cli FLUSHDB
```

---

## 📊 CSV Processing Issues

### Automated Import Problems

#### Symptoms:
- CSV files not being processed on Tuesday 8am
- Import errors in logs
- Data not appearing in dashboards after import

#### Diagnosis:
```bash
# Check scheduler status
curl http://localhost:6800/api/csv/import-status

# Check APScheduler logs
grep -i scheduler /opt/rfid3/logs/app.log

# Check CSV files directory
ls -la /opt/rfid3/app/shared/POR/
```

#### Solutions:

**Problem**: Scheduled imports not running
```bash
# Check if scheduler is active
python3 -c "
import sys
sys.path.append('/opt/rfid3/app')
from app.services.scheduler import scheduler
print(f'Scheduler running: {scheduler.running}')
print(f'Jobs: {scheduler.get_jobs()}')
"

# Restart application to restart scheduler
sudo systemctl restart rfid3
```

**Problem**: CSV file format errors
```bash
# Check CSV file integrity
python3 << 'PYTHON'
import pandas as pd
import glob

csv_files = glob.glob('/opt/rfid3/app/shared/POR/*.csv')
for file in csv_files:
    try:
        df = pd.read_csv(file)
        print(f"{file}: {len(df)} rows, {len(df.columns)} columns")
        print(f"  Null percentages: {(df.isnull().sum() / len(df) * 100).round(1).to_dict()}")
    except Exception as e:
        print(f"ERROR reading {file}: {e}")
PYTHON
```

**Problem**: Store marker attribution failing
```bash
# Manual CSV processing with detailed logging
python3 << 'PYTHON'
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
sys.path.append('/opt/rfid3/app')

from app.services.csv_import_service import CSVImportService
service = CSVImportService()

# Process with detailed output
try:
    result = service.import_scorecard_trends()
    print(f"Scorecard import result: {result}")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
PYTHON
```

---

## 🔐 Authentication & Access Issues

### API Access Problems

#### Symptoms:
- 401 Unauthorized errors
- Rate limiting errors (429)
- CORS errors in browser

#### Diagnosis:
```bash
# Test API access
curl -I http://localhost:6800/health
curl -I http://localhost:6800/api/inventory/dashboard_summary

# Check rate limiting
curl -v http://localhost:6800/tab/2 2>&1 | grep -i "rate-limit"
```

#### Solutions:

**Problem**: API returning 401 errors
```bash
# Check if API key authentication is enabled
grep -r "API_KEY" /opt/rfid3/app/config.py
grep -r "require_api_key" /opt/rfid3/app/

# Test without authentication first
curl http://localhost:6800/health
```

**Problem**: Rate limiting blocking requests
```bash
# Check rate limit configuration
grep -A 10 "RATELIMIT" /opt/rfid3/app/config.py

# Temporary solution: Clear rate limiting
redis-cli keys "*rate_limit*" | xargs redis-cli del

# Permanent solution: Adjust rate limits in config.py
```

---

## 🔧 System Configuration Issues

### Environment Configuration Problems

#### Symptoms:
- Application won't start
- Database connection errors
- Missing environment variables

#### Diagnosis:
```bash
# Check environment configuration
env | grep -E "(DB_|REDIS_|FLASK_)"
cat /opt/rfid3/app/.env.production

# Verify configuration loading
python3 -c "
import sys
sys.path.append('/opt/rfid3/app')
from config import DB_CONFIG
print(f'Database config: {DB_CONFIG}')
"
```

#### Solutions:

**Problem**: Environment variables not loading
```bash
# Check .env file existence and permissions
ls -la /opt/rfid3/app/.env*
sudo chown rfid3:rfid3 /opt/rfid3/app/.env.production

# Manual environment setup
export DB_HOST=localhost
export DB_USER=rfid_prod
export DB_PASSWORD=your_password
export DB_DATABASE=rfid_inventory_prod
export REDIS_URL=redis://localhost:6379/1
```

**Problem**: Configuration validation failing
```bash
# Test configuration manually
python3 << 'PYTHON'
import sys
sys.path.append('/opt/rfid3/app')

try:
    from config import validate_config
    validate_config()
    print("Configuration validation passed")
except Exception as e:
    print(f"Configuration validation failed: {e}")
    import traceback
    traceback.print_exc()
PYTHON
```

---

## 🚀 Deployment Issues

### Service Management Problems

#### Symptoms:
- Service fails to start
- Service crashes frequently
- Gunicorn workers dying

#### Diagnosis:
```bash
# Check service status
sudo systemctl status rfid3
sudo journalctl -u rfid3 -n 100 --no-pager

# Check Gunicorn processes
ps aux | grep gunicorn
pstree -p | grep gunicorn
```

#### Solutions:

**Problem**: Service fails to start
```bash
# Check systemd service file
sudo cat /etc/systemd/system/rfid3.service

# Test manual startup
sudo su - rfid3
cd /opt/rfid3/app
source venv/bin/activate
python run.py  # Test basic startup

# Check for permission issues
sudo chown -R rfid3:rfid3 /opt/rfid3
sudo chmod +x /opt/rfid3/app/run.py
```

**Problem**: Gunicorn workers dying
```bash
# Check Gunicorn configuration
cat /opt/rfid3/app/gunicorn.conf.py

# Check for memory issues
free -h
dmesg | grep -i "killed process"

# Adjust worker configuration
# Edit gunicorn.conf.py:
# workers = 2  # Reduce from 4 if memory is limited
# max_requests = 500  # Reduce from 1000
# timeout = 180  # Increase from 120
```

### Network & Proxy Issues

#### Symptoms:
- 502 Bad Gateway errors
- Connection timeouts
- Static files not loading

#### Diagnosis:
```bash
# Check Nginx status
sudo systemctl status nginx
sudo nginx -t

# Test direct application access
curl http://localhost:6800/health
curl http://localhost:6800/static/css/common.css
```

#### Solutions:

**Problem**: Nginx 502 Bad Gateway
```bash
# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Verify upstream connection
curl http://127.0.0.1:6800/health

# Check Nginx configuration
sudo nginx -t
sudo cat /etc/nginx/sites-enabled/rfid3
```

**Problem**: Static files 404 errors
```bash
# Verify static files directory
ls -la /opt/rfid3/app/static/
ls -la /opt/rfid3/app/static/css/

# Check Nginx static file configuration
grep -A 5 "location /static" /etc/nginx/sites-enabled/rfid3

# Fix permissions if needed
sudo chown -R www-data:www-data /opt/rfid3/app/static/
sudo chmod -R 644 /opt/rfid3/app/static/
sudo find /opt/rfid3/app/static/ -type d -exec chmod 755 {} \;
```

---

## 🔍 Monitoring & Alerting

### Log Analysis

#### Key Log Locations:
```bash
# Application logs
tail -f /opt/rfid3/logs/app.log
tail -f /opt/rfid3/logs/performance.log
tail -f /opt/rfid3/logs/csv_processing.log

# System logs
sudo journalctl -u rfid3 -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/mysql/error.log
```

#### Common Error Patterns:

**Database Connection Errors:**
```bash
# Look for these patterns in logs
grep -i "can't connect\|connection refused\|too many connections" /opt/rfid3/logs/app.log

# Solution: Check database status and restart if needed
sudo systemctl status mariadb
sudo systemctl restart mariadb
```

**Memory Errors:**
```bash
# Look for memory issues
grep -i "memory\|oom" /opt/rfid3/logs/app.log
dmesg | grep -i "killed process"

# Solution: Monitor memory usage and optimize
free -h
top -p $(pgrep -f rfid3)
```

**Performance Warnings:**
```bash
# Look for slow queries or timeouts
grep -i "slow\|timeout\|performance" /opt/rfid3/logs/app.log

# Solution: Check performance optimization status
curl http://localhost:6800/tab/2/performance_stats
```

---

## 🧪 Testing & Validation

### Comprehensive System Test

```bash
#!/bin/bash
# Complete system validation script

echo "=== RFID3 System Health Check ==="

# 1. Service status
echo "1. Checking service status..."
systemctl is-active rfid3 && echo "✓ Service running" || echo "✗ Service down"

# 2. Health endpoint
echo "2. Testing health endpoint..."
curl -s http://localhost:6800/health | jq '.status' | grep -q "healthy" && echo "✓ Health check passed" || echo "✗ Health check failed"

# 3. Database connectivity
echo "3. Testing database..."
mysql -u rfid_user -p -e "SELECT COUNT(*) FROM id_item_master;" rfid_inventory &>/dev/null && echo "✓ Database connected" || echo "✗ Database connection failed"

# 4. Redis connectivity
echo "4. Testing Redis..."
redis-cli ping | grep -q PONG && echo "✓ Redis connected" || echo "✗ Redis connection failed"

# 5. Tab 2 performance
echo "5. Testing Tab 2 performance..."
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:6800/tab/2)
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    echo "✓ Tab 2 performance good ($response_time seconds)"
else
    echo "⚠ Tab 2 performance slow ($response_time seconds)"
fi

# 6. API endpoints
echo "6. Testing API endpoints..."
curl -s http://localhost:6800/api/inventory/dashboard_summary | jq -e '.status' | grep -q "success" && echo "✓ API working" || echo "✗ API issues"

# 7. Cache performance
echo "7. Testing cache..."
hit_rate=$(redis-cli info stats | grep keyspace_hits: | cut -d: -f2)
if [ "$hit_rate" -gt 0 ]; then
    echo "✓ Cache active"
else
    echo "⚠ Cache not active"
fi

echo "=== System Check Complete ==="
```

### Performance Validation

```bash
# Run performance test suite
python tab2_performance_test.py

# Expected results:
# - Tab 2 load time: <2 seconds
# - Query reduction: >90%
# - Cache hit rate: >60%
# - Memory usage reduction: >80%
```

---

## 📞 Emergency Procedures

### System Down (Complete Failure)

#### Immediate Actions:
```bash
# 1. Check all services
sudo systemctl status rfid3 mariadb redis-server nginx

# 2. Restart in order
sudo systemctl start mariadb
sudo systemctl start redis-server
sudo systemctl start rfid3
sudo systemctl start nginx

# 3. Verify functionality
curl http://localhost:6800/health
curl http://your-domain.com/health  # If using domain
```

### Data Corruption

#### Emergency Data Recovery:
```bash
# 1. Stop application
sudo systemctl stop rfid3

# 2. Backup current state
mysqldump -u rfid_user -p rfid_inventory > /opt/rfid3/backups/emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from latest backup
mysql -u rfid_user -p rfid_inventory < /opt/rfid3/backups/rfid_db_backup_latest.sql

# 4. Restart application
sudo systemctl start rfid3

# 5. Verify data integrity
python comprehensive_database_correlation_analyzer.py
```

### Performance Emergency (>5 second response times)

#### Immediate Performance Recovery:
```bash
# 1. Clear all caches
redis-cli FLUSHALL
curl -X POST http://localhost:6800/tab/2/cache_clear

# 2. Restart application
sudo systemctl restart rfid3

# 3. Check database performance
mysql -u root -p << 'SQL'
SHOW PROCESSLIST;
KILL [slow_query_id];  -- Kill any long-running queries
SQL

# 4. Apply emergency performance settings
mysql -u root -p << 'SQL'
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB
SET GLOBAL query_cache_size = 134217728;  -- 128MB
SQL
```

---

## 📈 Performance Monitoring Commands

### Continuous Monitoring Script

```bash
#!/bin/bash
# Continuous performance monitoring

LOG_FILE="/opt/rfid3/logs/performance_monitor.log"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check response times
    tab2_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:6800/tab/2)
    api_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:6800/api/inventory/dashboard_summary)
    
    # Check system resources
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    memory_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    
    # Check database connections
    db_connections=$(mysql -u rfid_user -p -e "SHOW STATUS LIKE 'Threads_connected';" rfid_inventory 2>/dev/null | tail -1 | awk '{print $2}')
    
    # Log results
    echo "$timestamp,TAB2:${tab2_time}s,API:${api_time}s,CPU:${cpu_usage}%,MEM:${memory_usage}%,DB_CONN:$db_connections" >> $LOG_FILE
    
    # Alert if performance degrades
    if (( $(echo "$tab2_time > 3.0" | bc -l) )); then
        echo "ALERT: Tab 2 performance degraded: ${tab2_time}s" | tee -a $LOG_FILE
    fi
    
    sleep 60
done
```

---

**Troubleshooting Guide Status**: 🟢 Comprehensive | **Coverage**: 📊 Complete System  
**Last Updated**: September 1, 2025 | **Next Review**: October 1, 2025

This guide covers all major system components, common issues, and provides step-by-step solutions for maintaining optimal performance of the RFID3 system.
