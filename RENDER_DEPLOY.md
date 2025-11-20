# 🎨 Render Deployment Guide

## Quick Deploy to Render

### Step 1: Sign Up
Go to **https://render.com** and sign up (free)

### Step 2: Deploy with Blueprint
1. Click **"New +"** → **"Blueprint"**
2. Connect GitHub: `0prateeksingh0/product-importer`
3. Render detects `render.yaml` automatically
4. Click **"Apply"**

### Step 3: Add Redis
1. Click **"New +"** → **"Redis"**
2. Name: `product-importer-redis`
3. Plan: Free or Starter ($10/month)
4. Copy connection string

### Step 4: Update Environment Variables
Go to each service (web + worker) and add:
```
REDIS_URL=<paste-redis-connection-string>
CELERY_BROKER_URL=<same-as-redis-url>
CELERY_RESULT_BACKEND=<same-as-redis-url>
ALLOWED_ORIGINS=https://your-app.onrender.com
```

### Step 5: Access Your App
Your app URL: `https://product-importer-web.onrender.com`

## Pricing

**Free Tier:** $0/month (limited, services sleep)
**Starter Tier:** $31/month (recommended for 861k records)
- Web: $7/month
- Worker: $7/month  
- PostgreSQL: $7/month
- Redis: $10/month

## Verify Deployment

```bash
curl https://your-app.onrender.com/api/health
```

Done! 🎉

