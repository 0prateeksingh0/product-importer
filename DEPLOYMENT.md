# 🚢 Deployment Guide

This guide covers deploying the Product Importer application to various cloud platforms.

## Table of Contents
- [Heroku Deployment](#heroku-deployment)
- [Render Deployment](#render-deployment)
- [AWS Deployment](#aws-deployment)
- [Digital Ocean](#digital-ocean)
- [Environment Configuration](#environment-configuration)

---

## Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Git repository initialized
- Heroku account

### Step-by-Step Guide

1. **Install Heroku CLI** (if not already installed)
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   heroku create product-importer-acme
   # Or use: heroku create (generates random name)
   ```

4. **Add PostgreSQL Database**
   ```bash
   # For free tier (limited)
   heroku addons:create heroku-postgresql:essential-0
   
   # For production (paid)
   heroku addons:create heroku-postgresql:standard-0
   ```

5. **Add Redis**
   ```bash
   # For free tier (limited)
   heroku addons:create heroku-redis:mini
   
   # For production (paid)
   heroku addons:create heroku-redis:premium-0
   ```

6. **Configure Environment Variables**
   ```bash
   # Heroku automatically sets DATABASE_URL and REDIS_URL
   
   # Set additional variables
   heroku config:set SECRET_KEY="your-secure-random-key-here"
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_ORIGINS="https://product-importer-acme.herokuapp.com"
   
   # Redis URL for Celery (same as REDIS_URL)
   heroku config:set CELERY_BROKER_URL=$(heroku config:get REDIS_URL)
   heroku config:set CELERY_RESULT_BACKEND=$(heroku config:get REDIS_URL)
   ```

7. **Deploy the Application**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

8. **Scale Workers**
   ```bash
   # Start web dyno (should be automatic)
   heroku ps:scale web=1
   
   # Start Celery worker
   heroku ps:scale worker=1
   ```

9. **Initialize Database**
   ```bash
   # The database tables are created automatically on first run
   # Check logs to verify
   heroku logs --tail
   ```

10. **Open Application**
    ```bash
    heroku open
    ```

### Monitoring Heroku

```bash
# View logs
heroku logs --tail

# Check dyno status
heroku ps

# View database info
heroku pg:info

# View Redis info
heroku redis:info
```

### Important Notes for Heroku

- **30-second timeout**: Large imports run in background workers (Celery), so they're not affected
- **Ephemeral filesystem**: Uploaded files are temporary; deleted after processing
- **Free tier limitations**: 
  - Web dyno sleeps after 30 min inactivity
  - 1000 hours/month limit
  - Database: 10,000 rows limit
  - Redis: 25MB limit

---

## Render Deployment

### Prerequisites
- Render account
- GitHub/GitLab repository

### Step-by-Step Guide

1. **Push Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create New Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: product-importer
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: product-importer-db
   - Plan: Free or Starter
   - Copy the Internal Database URL

4. **Add Redis**
   - Click "New +" → "Redis"
   - Name: product-importer-redis
   - Plan: Free or Starter
   - Copy the Internal Redis URL

5. **Add Background Worker**
   - Click "New +" → "Background Worker"
   - Connect same repository
   - **Start Command**: `celery -A app.celery_app worker --loglevel=info`

6. **Configure Environment Variables** (in Web Service settings)
   ```
   DATABASE_URL=<internal-database-url>
   REDIS_URL=<internal-redis-url>
   CELERY_BROKER_URL=<internal-redis-url>
   CELERY_RESULT_BACKEND=<internal-redis-url>
   SECRET_KEY=<generate-secure-key>
   DEBUG=False
   ALLOWED_ORIGINS=https://product-importer.onrender.com
   ```

7. **Deploy**
   - Render automatically deploys on git push
   - First deployment may take 5-10 minutes

### Monitoring Render

- View logs in the Render dashboard
- Check metrics for CPU, memory usage
- Set up email alerts for failures

---

## AWS Deployment (Docker)

### Prerequisites
- AWS account
- AWS CLI installed
- Docker installed

### Using AWS ECS (Elastic Container Service)

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name product-importer
   ```

2. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build image
   docker build -t product-importer .
   
   # Tag image
   docker tag product-importer:latest \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com/product-importer:latest
   
   # Push image
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/product-importer:latest
   ```

3. **Create RDS PostgreSQL Database**
   - Use AWS Console or CLI
   - Note down endpoint, username, password

4. **Create ElastiCache Redis**
   - Use AWS Console or CLI
   - Note down endpoint

5. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name product-importer-cluster
   ```

6. **Create Task Definition**
   - Define web service and worker tasks
   - Set environment variables
   - Configure resource limits

7. **Create ECS Service**
   - Launch tasks in cluster
   - Configure load balancer
   - Set up auto-scaling

### Using AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB Application**
   ```bash
   eb init -p docker product-importer
   ```

3. **Create Environment**
   ```bash
   eb create product-importer-env
   ```

4. **Configure Environment Variables**
   ```bash
   eb setenv DATABASE_URL="..." REDIS_URL="..." SECRET_KEY="..."
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

---

## Digital Ocean Deployment

### Using App Platform

1. **Push to GitHub**
2. **Create New App**
   - Connect GitHub repository
   - Select "Web Service"
   - Auto-detected as Python

3. **Add Database**
   - Add PostgreSQL database component
   - Add Redis database component

4. **Add Worker**
   - Add Worker component
   - Set command: `celery -A app.celery_app worker --loglevel=info`

5. **Configure Environment Variables**
   - Set via App Platform UI

6. **Deploy**
   - Automatic on git push

---

## Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis
REDIS_URL=redis://host:port/0

# Celery
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0

# Application
SECRET_KEY=<generate-secure-random-key>
DEBUG=False
ALLOWED_ORIGINS=https://your-domain.com

# Optional
MAX_UPLOAD_SIZE=104857600
BATCH_SIZE=1000
```

### Generating Secure Secret Key

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Post-Deployment Checklist

- [ ] Application loads without errors
- [ ] Database tables created successfully
- [ ] Can create products manually
- [ ] CSV import works and shows progress
- [ ] Webhooks can be configured
- [ ] Webhook test sends successfully
- [ ] Search and filters work
- [ ] Pagination functions correctly
- [ ] SSL/HTTPS is enabled
- [ ] Environment variables are set correctly
- [ ] Worker processes are running
- [ ] Logs are accessible
- [ ] Monitoring is set up

---

## Troubleshooting

### Application won't start
- Check logs for error messages
- Verify all environment variables are set
- Ensure database and Redis are accessible
- Check Python version matches requirements

### Import not working
- Verify Celery worker is running
- Check worker logs
- Ensure Redis connection is working
- Verify database write permissions

### Webhooks not firing
- Check worker logs for errors
- Verify webhook URL is accessible from server
- Check firewall rules
- Test webhook endpoint manually

### Database connection errors
- Verify DATABASE_URL format
- Check database server is running
- Verify network access / security groups
- Check SSL requirements

---

## Scaling Considerations

### For Production Traffic

1. **Horizontal Scaling**
   - Increase number of web dynos/instances
   - Add more Celery workers
   - Use database read replicas

2. **Caching**
   - Implement Redis caching for frequent queries
   - Use CDN for static assets

3. **Database Optimization**
   - Add additional indexes as needed
   - Regular VACUUM and ANALYZE
   - Connection pooling (already configured)

4. **File Storage**
   - Use S3 or equivalent for CSV storage
   - Implement cleanup for old imports

5. **Monitoring**
   - Set up error tracking (Sentry)
   - Application performance monitoring (New Relic, DataDog)
   - Database monitoring
   - Alert on high error rates

---

## Cost Optimization

### Free Tier Options

- **Heroku**: Free tier available (with limitations)
- **Render**: 750 hours/month free
- **Railway**: $5 free credit monthly
- **Fly.io**: Generous free tier

### Paid Recommendations

For production with 500k records:
- **Render**: ~$25/month (Starter tier)
- **Heroku**: ~$32/month (Hobby tier)
- **AWS**: ~$50-100/month (t3.small + RDS + ElastiCache)
- **Digital Ocean**: ~$40/month (App Platform Pro)

---

## Support

For deployment issues, check:
1. Application logs
2. Worker logs
3. Database connectivity
4. Redis connectivity
5. Environment variables

Contact: [your-email@example.com]

