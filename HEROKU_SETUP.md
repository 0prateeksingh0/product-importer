# 🚀 Heroku Deployment Instructions

This guide will help you deploy the Product Importer to Heroku in just a few minutes.

## Prerequisites

1. **Heroku Account** - Sign up at https://heroku.com
2. **Heroku CLI** - Install from https://devcenter.heroku.com/articles/heroku-cli
3. **Git** - Ensure your project is in a Git repository

## Quick Deploy (5 Minutes)

### Step 1: Login to Heroku

```bash
heroku login
```

This will open your browser for authentication.

### Step 2: Create a New Heroku App

```bash
cd "/Users/tronadoit/Desktop/Product Importer"
heroku create product-importer-acme
# Or let Heroku generate a random name:
# heroku create
```

**Note the app URL** - it will be something like `https://product-importer-acme.herokuapp.com`

### Step 3: Add PostgreSQL and Redis Add-ons

```bash
# Add PostgreSQL database (free tier: 10,000 rows limit, paid tier recommended for 500k records)
heroku addons:create heroku-postgresql:essential-0

# Add Redis for Celery (free tier: 25MB, paid tier recommended for production)
heroku addons:create heroku-redis:mini
```

**For production with 500k+ records, use:**
```bash
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0
```

### Step 4: Set Environment Variables

```bash
# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Set environment variables
heroku config:set SECRET_KEY="$SECRET_KEY"
heroku config:set DEBUG=False
heroku config:set ALLOWED_ORIGINS="https://$(heroku info -s | grep web_url | cut -d= -f2)"

# Celery configuration (automatically use Heroku's Redis URL)
heroku config:set CELERY_BROKER_URL=$(heroku config:get REDIS_URL)
heroku config:set CELERY_RESULT_BACKEND=$(heroku config:get REDIS_URL)
```

### Step 5: Initialize Git and Deploy

```bash
# If not already initialized
git init
git add .
git commit -m "Initial commit for Heroku deployment"

# Add Heroku remote (if not done in step 2)
heroku git:remote -a product-importer-acme

# Deploy to Heroku
git push heroku main
# Or if you're on master branch:
# git push heroku master:main
```

### Step 6: Scale Workers

```bash
# Ensure web dyno is running (should be automatic)
heroku ps:scale web=1

# Start Celery worker for background tasks
heroku ps:scale worker=1
```

### Step 7: Verify Deployment

```bash
# Open the app in browser
heroku open

# Check logs
heroku logs --tail

# Check dyno status
heroku ps
```

## Post-Deployment Checklist

- [ ] App opens in browser without errors
- [ ] Can navigate between tabs (Import, Products, Webhooks)
- [ ] Database tables created automatically
- [ ] Can create products manually
- [ ] Can upload CSV file (test with small file first)
- [ ] Real-time progress updates work
- [ ] Webhooks can be configured and tested

## Important Notes

### Heroku Limitations

1. **30-Second Timeout**: HTTP requests timeout after 30 seconds
   - ✅ **Solution**: Long-running imports are handled by Celery workers (no timeout)

2. **Ephemeral Filesystem**: Uploaded files are temporary
   - ✅ **Solution**: Files are deleted after processing

3. **Free Tier Limits**:
   - Web dyno sleeps after 30 min inactivity
   - 1000 dyno hours/month
   - Database: 10,000 rows (upgrade to standard-0 for 500k records)
   - Redis: 25MB (upgrade for production)

### Recommended Upgrades for Production

```bash
# Upgrade database for 500,000 records
heroku addons:upgrade heroku-postgresql:standard-0

# Upgrade Redis for better performance
heroku addons:upgrade heroku-redis:premium-0

# Use Hobby dynos (no sleep)
heroku dyno:type hobby -a product-importer-acme
```

**Estimated cost**: ~$32/month (Hobby dynos + Standard PostgreSQL + Premium Redis)

## Configuration Updates

### Update CORS Origins

After deployment, update CORS to allow your Heroku domain:

```bash
heroku config:set ALLOWED_ORIGINS="https://your-app-name.herokuapp.com"
```

### Increase Worker Concurrency (for faster imports)

Edit `Procfile` and increase `--concurrency`:
```
worker: celery -A app.celery_app worker --loglevel=info --concurrency=4
```

Then redeploy:
```bash
git add Procfile
git commit -m "Increase worker concurrency"
git push heroku main
```

## Monitoring

### View Logs
```bash
# Real-time logs
heroku logs --tail

# Web dyno logs only
heroku logs --source app --tail

# Worker logs only
heroku logs --source worker --tail
```

### Check Database
```bash
# Database info
heroku pg:info

# Connect to database
heroku pg:psql
```

### Check Redis
```bash
# Redis info
heroku redis:info

# Redis CLI
heroku redis:cli
```

### View Dyno Metrics
```bash
heroku ps
heroku ps:type
```

## Testing Your Deployed App

### 1. Test with Small CSV First

Create a test CSV with 100 products:
```csv
sku,name,description,price
TEST001,Test Product 1,Description 1,10.99
TEST002,Test Product 2,Description 2,20.99
```

Upload and verify progress tracking works.

### 2. Test with Large CSV

Upload your `products.csv` (861k records) and monitor:
- Progress updates in real-time
- Worker logs: `heroku logs --source worker --tail`
- Ensure no timeouts (handled by Celery)

### 3. Test Webhooks

Use https://webhook.site to create a test endpoint:
1. Go to https://webhook.site
2. Copy your unique URL
3. Create webhook in app with that URL
4. Trigger an event (create product)
5. Verify webhook received the payload

## Troubleshooting

### App Won't Start
```bash
# Check logs for errors
heroku logs --tail

# Verify buildpack
heroku buildpacks
# Should show: heroku/python

# Check Procfile exists
cat Procfile
```

### Database Connection Errors
```bash
# Verify DATABASE_URL is set
heroku config:get DATABASE_URL

# Check database status
heroku pg:info
```

### Worker Not Processing Jobs
```bash
# Check if worker is running
heroku ps

# Check worker logs
heroku logs --source worker --tail

# Restart worker
heroku ps:restart worker
```

### Import Stuck at "Processing"
```bash
# Check worker logs
heroku logs --source worker --tail

# Verify Redis is working
heroku redis:info

# Restart worker
heroku ps:restart worker
```

### "Out of Memory" Errors
```bash
# Upgrade dyno size
heroku ps:resize web=standard-1x
heroku ps:resize worker=standard-1x
```

## Database Management

### Backup Database
```bash
heroku pg:backups:capture
heroku pg:backups:download
```

### Reset Database (CAREFUL!)
```bash
heroku pg:reset DATABASE_URL --confirm your-app-name
```

### Run SQL Query
```bash
heroku pg:psql
# Then run SQL:
SELECT COUNT(*) FROM products;
```

## Custom Domain (Optional)

```bash
# Add custom domain
heroku domains:add www.yourdomain.com

# Get DNS target
heroku domains

# Update your DNS provider with the CNAME record
```

## Continuous Deployment

### Enable GitHub Integration

1. Go to Heroku Dashboard
2. Select your app
3. Go to "Deploy" tab
4. Connect to GitHub
5. Enable "Automatic Deploys" from main branch

Now every push to GitHub will auto-deploy to Heroku!

## Scaling for High Traffic

### Horizontal Scaling
```bash
# Add more web dynos
heroku ps:scale web=2

# Add more workers for concurrent imports
heroku ps:scale worker=2
```

### Vertical Scaling
```bash
# Use more powerful dynos
heroku ps:resize web=performance-m
heroku ps:resize worker=performance-m
```

## Cost Optimization

### Free Tier (Development)
- Cost: $0/month
- Limitations: Dyno sleep, 10k DB rows, 25MB Redis

### Hobby Tier (Small Production)
- Cost: ~$32/month
- No dyno sleep, 10M DB rows, 100MB Redis

### Production Tier
- Cost: ~$200+/month
- High availability, autoscaling, dedicated resources

## Useful Commands Cheatsheet

```bash
# Deployment
heroku login
heroku create
git push heroku main

# Logs
heroku logs --tail
heroku logs --source app
heroku logs --source worker

# Dynos
heroku ps
heroku ps:restart
heroku ps:scale worker=2

# Database
heroku pg:info
heroku pg:psql
heroku pg:backups:capture

# Redis
heroku redis:info
heroku redis:cli

# Config
heroku config
heroku config:set KEY=VALUE
heroku config:get DATABASE_URL

# App Management
heroku open
heroku apps:info
heroku maintenance:on
heroku maintenance:off
```

## Need Help?

- **Heroku Docs**: https://devcenter.heroku.com/
- **Heroku Support**: https://help.heroku.com/
- **Project Issues**: [GitHub Issues Link]

---

🎉 **You're all set!** Your Product Importer is now live on Heroku!

Share your deployment URL: `https://your-app-name.herokuapp.com`

