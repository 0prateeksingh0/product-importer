# 🎨 Complete Render Deployment Guide

## 🎯 Why Render?

✅ **Free Tier** - Free PostgreSQL & Redis (with limits)
✅ **Easy Setup** - Auto-detection and Blueprint
✅ **No Credit Card** - Free tier doesn't require CC
✅ **Fast Deployments** - Faster than Heroku
✅ **Great for Portfolios** - Professional deployment

---

## 📦 Prerequisites

- ✅ Code on GitHub: `https://github.com/0prateeksingh0/product-importer`
- ✅ Render account (free): `https://render.com`

---

## 🚀 DEPLOYMENT METHOD 1: Blueprint (Automated - Recommended)

### Step 1: Push render.yaml to GitHub

Your `render.yaml` is already in the repo. Just push it:

```bash
cd "/Users/tronadoit/Desktop/Product Importer"
git add render.yaml build.sh
git commit -m "Add Render configuration"
git push origin main
```

### Step 2: Deploy with Blueprint

1. Go to **https://dashboard.render.com**
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub: `0prateeksingh0/product-importer`
4. Render will detect `render.yaml` automatically
5. Click **"Apply"**
6. Wait 5-10 minutes for deployment
7. ✅ Done!

**Render will automatically create:**
- Web service (FastAPI)
- Worker service (Celery)
- PostgreSQL database
- You'll need to add Redis manually (see below)

---

## 🚀 DEPLOYMENT METHOD 2: Manual Setup (Step-by-Step)

### Step 1: Create PostgreSQL Database

1. Go to **https://dashboard.render.com**
2. Click **"New +"** → **"PostgreSQL"**
3. Fill in:
   - **Name**: `product-importer-db`
   - **Database**: `product_importer`
   - **User**: `product_importer`
   - **Region**: `Oregon` (or closest to you)
   - **Plan**: `Free` (for testing) or `Starter` ($7/month for production)
4. Click **"Create Database"**
5. **Save the connection strings** (Internal & External)

### Step 2: Create Redis Instance

1. Click **"New +"** → **"Redis"**
2. Fill in:
   - **Name**: `product-importer-redis`
   - **Region**: Same as database
   - **Plan**: `Free` (limited) or `Starter` ($10/month)
3. Click **"Create Redis"**
4. **Save the connection string**

### Step 3: Create Web Service (FastAPI)

1. Click **"New +"** → **"Web Service"**
2. Connect GitHub repository: `0prateeksingh0/product-importer`
3. Fill in:
   - **Name**: `product-importer-web`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free` (for testing) or `Starter` ($7/month)

4. Click **"Advanced"** and add Environment Variables:

```
PYTHON_VERSION = 3.11.6
SECRET_KEY = [Generate random: python3 -c "import secrets; print(secrets.token_urlsafe(32))"]
DEBUG = False
DATABASE_URL = [Paste from PostgreSQL Internal Connection String]
REDIS_URL = [Paste from Redis Connection String]
CELERY_BROKER_URL = [Same as REDIS_URL]
CELERY_RESULT_BACKEND = [Same as REDIS_URL]
ALLOWED_ORIGINS = https://product-importer-web.onrender.com
```

5. Click **"Create Web Service"**

### Step 4: Create Background Worker (Celery)

1. Click **"New +"** → **"Background Worker"**
2. Connect same GitHub repository
3. Fill in:
   - **Name**: `product-importer-worker`
   - **Region**: Same as others
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A app.celery_app worker --loglevel=info --concurrency=2`
   - **Plan**: `Free` or `Starter` ($7/month)

4. Add the **same Environment Variables** as web service

5. Click **"Create Background Worker"**

---

## ⚙️ Environment Variables Reference

Copy these to BOTH web service and worker:

```bash
PYTHON_VERSION=3.11.6
SECRET_KEY=<generate-with-python3 -c "import secrets; print(secrets.token_urlsafe(32))">
DEBUG=False
DATABASE_URL=<from-postgresql-internal-connection-string>
REDIS_URL=<from-redis-connection-string>
CELERY_BROKER_URL=<same-as-redis-url>
CELERY_RESULT_BACKEND=<same-as-redis-url>
ALLOWED_ORIGINS=https://product-importer-web.onrender.com,https://your-custom-domain.com
```

---

## 🌐 Get Your App URL

1. Go to your web service dashboard
2. Find the URL at the top: `https://product-importer-web.onrender.com`
3. Click to open your app!

---

## ✅ Verify Deployment

### Test 1: Health Check
```bash
curl https://product-importer-web.onrender.com/api/health
```

Should return:
```json
{"status":"healthy","timestamp":"2025-11-20T..."}
```

### Test 2: API Documentation
Open in browser:
```
https://product-importer-web.onrender.com/docs
```

### Test 3: Create a Product
```bash
curl -X POST https://product-importer-web.onrender.com/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST001",
    "name": "Test Product",
    "description": "Testing Render deployment",
    "price": "99.99",
    "active": true
  }'
```

### Test 4: Upload CSV via Web UI
1. Go to `https://product-importer-web.onrender.com`
2. Click "Import Products" tab
3. Upload a small CSV file
4. Watch real-time progress!

---

## 📊 Monitor Your Services

### View Logs
1. Go to service dashboard
2. Click **"Logs"** tab
3. Real-time logs appear

### Check Service Status
- **Web service**: Should show "Live"
- **Worker service**: Should show "Live"
- **Database**: Should show "Available"
- **Redis**: Should show "Available"

### View Metrics
- CPU usage
- Memory usage
- Request count
- Response times

---

## 🔄 Auto-Deploy on Git Push

Render automatically deploys when you push to GitHub:

```bash
cd "/Users/tronadoit/Desktop/Product Importer"

# Make changes
# Edit files...

# Commit and push
git add .
git commit -m "Update feature"
git push origin main

# Render automatically deploys! 🎉
# Watch logs in Render dashboard
```

---

## 💰 Render Pricing

### Free Tier
- **Web Service**: Free (spins down after 15 min inactivity)
- **PostgreSQL**: Free (limited to 256MB)
- **Redis**: Free (limited to 25MB)
- **Background Worker**: Free (limited hours)
- **Total**: $0/month

**Limitations:**
- Services sleep after inactivity
- Limited database size (good for ~10k products)
- Worker has hour limits

### Starter Tier (Production - Recommended for 861k records)
- **Web Service**: $7/month (always on)
- **Background Worker**: $7/month (always on)
- **PostgreSQL Starter**: $7/month (1GB storage)
- **Redis Starter**: $10/month (256MB)
- **Total**: $31/month

### Pro Tier (High Traffic)
- **Web Service**: $25/month (4GB RAM)
- **Worker**: $25/month
- **PostgreSQL Pro**: $25/month (10GB)
- **Redis Pro**: $25/month (1GB)
- **Total**: $100/month

**For your 861k products, use Starter tier ($31/month)**

---

## 🎨 Custom Domain (Optional)

1. Go to web service → **"Settings"** → **"Custom Domain"**
2. Click **"Add Custom Domain"**
3. Enter: `products.yourdomain.com`
4. Render gives you CNAME record
5. Add to your DNS provider:
   ```
   CNAME: products → product-importer-web.onrender.com
   ```
6. SSL certificate auto-generated (free)!

---

## 🔧 Troubleshooting

### Problem: Service won't start
**Solution:**
```bash
# Check build logs in Render dashboard
# Look for Python errors
# Verify requirements.txt is correct
```

### Problem: Database connection error
**Solution:**
```bash
# Verify DATABASE_URL is set correctly
# Use INTERNAL connection string, not external
# Check database is in same region as services
```

### Problem: Worker not processing jobs
**Solution:**
```bash
# Check worker service logs
# Verify REDIS_URL is set in worker
# Verify CELERY_BROKER_URL = REDIS_URL
# Restart worker service
```

### Problem: CSV import fails
**Solution:**
```bash
# Check worker logs for errors
# Verify both web and worker have same environment variables
# Check Redis connection
# Verify file upload size limits
```

### Problem: Services sleeping (Free tier)
**Solution:**
```bash
# Upgrade to Starter plan ($7/month per service)
# Or use a cron job to ping every 14 minutes
# Add to your local cron:
# */14 * * * * curl https://product-importer-web.onrender.com/api/health
```

---

## 🔐 Security Checklist

Before going live:

- ✅ Set `DEBUG=False`
- ✅ Use strong `SECRET_KEY` (random 32+ chars)
- ✅ Set correct `ALLOWED_ORIGINS`
- ✅ Use INTERNAL database URL (not external)
- ✅ Enable SSL (automatic on Render)
- ✅ Don't commit `.env` file
- ✅ Use environment variables for all secrets

---

## 📈 Performance Tips

### For 861k Products:

1. **Use Starter Plan** (not free)
   - More consistent performance
   - No sleeping
   - Better database

2. **Optimize Worker**
   ```
   Start Command: celery -A app.celery_app worker --loglevel=info --concurrency=4
   ```
   (Increase concurrency from 2 to 4)

3. **Scale Services** (if needed)
   - Add more worker instances
   - Upgrade to higher plans

4. **Database Optimization**
   - Upgrade to Pro plan for larger database
   - Add database indices (already done in models.py)

---

## 🔄 Update Your Deployment

### Update Code
```bash
git add .
git commit -m "Update feature"
git push origin main
# Render auto-deploys
```

### Update Environment Variables
1. Go to service → "Environment"
2. Click variable to edit
3. Save
4. Service auto-redeploys

### Manual Redeploy
1. Go to service dashboard
2. Click "Manual Deploy" → "Deploy latest commit"

---

## 📱 Render Dashboard Features

### Logs
- Real-time streaming
- Filter by severity
- Search logs
- Download logs

### Metrics
- CPU usage over time
- Memory usage
- Request rate
- Error rate

### Shell Access
- Click "Shell" tab
- Run commands in container
- Debug issues

### Events
- Deployment history
- Service events
- Database backups

---

## 🎯 Complete Setup Checklist

- [ ] Created Render account
- [ ] Created PostgreSQL database
- [ ] Created Redis instance
- [ ] Created web service (FastAPI)
- [ ] Created background worker (Celery)
- [ ] Set all environment variables (both services)
- [ ] Verified all services are "Live"
- [ ] Tested health endpoint
- [ ] Tested API endpoints
- [ ] Tested CSV upload
- [ ] Checked logs for errors
- [ ] Noted down app URL

---

## 📧 For Assignment Submission

**Include in your email:**

1. **GitHub Repository:**
   ```
   https://github.com/0prateeksingh0/product-importer
   ```

2. **Live Render URL:**
   ```
   https://product-importer-web.onrender.com
   ```

3. **API Documentation:**
   ```
   https://product-importer-web.onrender.com/docs
   ```

4. **Brief Description:**
   ```
   Product Importer deployed on Render
   
   Live Application: https://product-importer-web.onrender.com
   
   Tech Stack:
   - FastAPI (Python web framework)
   - Celery + Redis (async background processing)
   - SQLAlchemy + PostgreSQL (database ORM)
   - Server-Sent Events (real-time progress)
   - Docker support (included)
   
   Features:
   ✅ CSV import with real-time progress (tested with 861k records)
   ✅ Complete product CRUD operations
   ✅ Search, filtering, and pagination
   ✅ Webhook configuration and testing
   ✅ Bulk operations with confirmation
   ✅ Modern responsive UI
   
   All 4 assignment stories fully implemented.
   
   Architecture:
   - Web service: FastAPI REST API
   - Worker service: Celery for async tasks
   - PostgreSQL: Product and job data
   - Redis: Message broker for Celery
   
   Documentation included:
   - Complete README.md
   - Architecture documentation
   - Deployment guides for Render, Heroku, Railway
   - Docker Compose for local development
   ```

---

## 🆚 Render vs Other Platforms

| Feature | Render | Heroku | Railway |
|---------|--------|--------|---------|
| **Free Tier** | Yes (limited) | Limited | $5 credit |
| **Setup** | Easy | Medium | Easiest |
| **Cost (Starter)** | $31/month | $79/month | $30/month |
| **Auto-deploy** | ✅ Yes | ✅ Yes | ✅ Yes |
| **PostgreSQL** | Built-in | Add-on | Built-in |
| **Redis** | Built-in | Add-on | Built-in |
| **Custom Domain** | Free SSL | Free SSL | Free SSL |
| **Logs** | Great UI | CLI-based | Great UI |
| **Learning Curve** | Easy | Medium | Easy |

**Render is great for portfolios and production!** 🎨

---

## 🎉 You're Done!

Your app is live on Render at:
```
https://product-importer-web.onrender.com
```

Test it, submit it, and you're all set! 🚀

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Your Deployment Guides**: See DEPLOYMENT.md, HEROKU_SETUP.md, etc.

