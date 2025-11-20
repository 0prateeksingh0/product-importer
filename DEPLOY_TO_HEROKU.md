# 🚀 Deploy to Heroku - Step by Step

## ✅ Prerequisites

1. **Heroku Account**: Sign up at https://heroku.com (free)
2. **Heroku CLI**: Install from https://devcenter.heroku.com/articles/heroku-cli
3. **Git**: Should already be installed on Mac

---

## 📦 Step 1: Initialize Git Repository

```bash
cd "/Users/tronadoit/Desktop/Product Importer"

# Initialize git
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit - Product Importer for Acme Inc"
```

---

## 🔑 Step 2: Login to Heroku

```bash
heroku login
```

This will open your browser for authentication.

---

## 🎯 Step 3: Create Heroku App

```bash
# Create with custom name
heroku create product-importer-acme

# OR let Heroku generate a random name
heroku create
```

**Save your app URL** - it will be something like:
`https://product-importer-acme.herokuapp.com`

---

## 🗄️ Step 4: Add PostgreSQL Database

```bash
# For testing (free tier - 10,000 rows limit)
heroku addons:create heroku-postgresql:essential-0

# For production with 861k rows (recommended)
heroku addons:create heroku-postgresql:standard-0
```

**Cost**: 
- Essential: $5/month (10k rows max)
- Standard: $50/month (10M rows)

For your 861k CSV, use **Standard**!

---

## 🔴 Step 5: Add Redis for Celery

```bash
# For testing (free tier - 25MB)
heroku addons:create heroku-redis:mini

# For production (recommended)
heroku addons:create heroku-redis:premium-0
```

**Cost**:
- Mini: Free (25MB)
- Premium-0: $15/month (100MB)

---

## ⚙️ Step 6: Set Environment Variables

```bash
# Generate secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Set all config vars
heroku config:set SECRET_KEY="$SECRET_KEY"
heroku config:set DEBUG=False
heroku config:set ALLOWED_ORIGINS="https://$(heroku info -s | grep web_url | cut -d= -f2 | sed 's|https://||' | sed 's|/||')"

# Set Celery URLs (uses Redis)
heroku config:set CELERY_BROKER_URL=$(heroku config:get REDIS_URL)
heroku config:set CELERY_RESULT_BACKEND=$(heroku config:get REDIS_URL)

# Verify configuration
heroku config
```

---

## 🚢 Step 7: Deploy to Heroku

```bash
# Push code to Heroku
git push heroku main

# Or if you're on master branch:
git push heroku master:main
```

**Wait for build to complete** (2-3 minutes)

---

## 👷 Step 8: Scale Workers

```bash
# Start web dyno (usually automatic)
heroku ps:scale web=1

# Start Celery worker (IMPORTANT for CSV imports!)
heroku ps:scale worker=1
```

**Cost**: 
- Free tier: 1000 dyno hours/month (enough for 1 web + 1 worker)
- Hobby: $7/dyno/month (no sleep, unlimited hours)

---

## ✅ Step 9: Open Your App

```bash
heroku open
```

Your app should open in the browser!

---

## 🧪 Step 10: Test Your Deployment

### Test 1: Health Check
```bash
curl https://your-app-name.herokuapp.com/api/health
```

### Test 2: Create a Product
```bash
curl -X POST https://your-app-name.herokuapp.com/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST001",
    "name": "Test Product",
    "description": "Testing Heroku deployment",
    "price": "99.99",
    "active": true
  }'
```

### Test 3: Upload CSV (via Web UI)
1. Go to your app URL
2. Click "Import Products" tab
3. Upload `products.csv`
4. Watch real-time progress!

---

## 📊 Step 11: Monitor Your App

```bash
# View logs (real-time)
heroku logs --tail

# View web logs only
heroku logs --source app --tail

# View worker logs only
heroku logs --source worker --tail

# Check dyno status
heroku ps

# View database info
heroku pg:info

# View Redis info
heroku redis:info
```

---

## 🔧 Troubleshooting

### Problem: App crashes on startup

**Solution**: Check logs
```bash
heroku logs --tail
```

Common issues:
- Missing environment variables
- Database connection failed
- Missing dependencies

### Problem: CSV import doesn't work

**Solution**: Make sure worker dyno is running
```bash
heroku ps
# Should show: worker.1: up

# If not running:
heroku ps:scale worker=1
```

### Problem: Worker not processing jobs

**Solution**: Check worker logs
```bash
heroku logs --source worker --tail
```

Restart worker:
```bash
heroku ps:restart worker
```

### Problem: Database connection errors

**Solution**: Verify DATABASE_URL is set
```bash
heroku config:get DATABASE_URL
```

### Problem: Out of memory

**Solution**: Upgrade dyno type
```bash
heroku ps:resize web=standard-1x
heroku ps:resize worker=standard-1x
```

---

## 💰 Cost Summary

### Minimal Setup (Testing)
- App: Free
- PostgreSQL Essential: $5/month
- Redis Mini: Free
- **Total: $5/month**

**Limitation**: 10k products max

### Recommended Setup (Production - 861k rows)
- Web Dyno (Hobby): $7/month
- Worker Dyno (Hobby): $7/month
- PostgreSQL Standard-0: $50/month
- Redis Premium-0: $15/month
- **Total: $79/month**

### Free Tier (Development Only)
- Everything free
- **Limitations**:
  - Dyno sleeps after 30 min inactivity
  - 1000 dyno hours/month total
  - 10k row database limit
  - 25MB Redis limit

---

## 🔄 Update Your Deployed App

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Description of changes"

# Push to Heroku
git push heroku main

# Check deployment
heroku logs --tail
```

---

## 🌐 Custom Domain (Optional)

```bash
# Add your domain
heroku domains:add www.yourdomain.com

# Get DNS target
heroku domains

# Add CNAME record in your DNS provider:
# CNAME: www -> your-app-name.herokuapp.com
```

---

## 📈 Performance Tips

### For Large CSV (861k rows)

1. **Use Standard PostgreSQL** (not Essential)
2. **Use Premium Redis** (not Mini)
3. **Use Hobby or Standard dynos** (not free)
4. **Increase worker concurrency**:

Edit `Procfile`:
```
worker: celery -A app.celery_app worker --loglevel=info --concurrency=4
```

Then deploy:
```bash
git add Procfile
git commit -m "Increase worker concurrency"
git push heroku main
```

5. **Scale multiple workers** (if needed):
```bash
heroku ps:scale worker=2
```

---

## 🔐 Security Checklist

Before going live:

- ✅ SECRET_KEY is set to a random string
- ✅ DEBUG is set to False
- ✅ ALLOWED_ORIGINS includes your Heroku domain
- ✅ PostgreSQL connection is secure (SSL enabled by default)
- ✅ No sensitive data in git history

---

## 📚 Useful Heroku Commands

```bash
# Restart app
heroku restart

# Run one-off commands
heroku run python

# Access database
heroku pg:psql

# Backup database
heroku pg:backups:capture
heroku pg:backups:download

# View environment variables
heroku config

# Set environment variable
heroku config:set KEY=VALUE

# Delete environment variable
heroku config:unset KEY

# Check app info
heroku info

# Open Heroku dashboard
heroku open --app
```

---

## ✅ Deployment Checklist

- [ ] Git repository initialized
- [ ] Committed all files
- [ ] Logged into Heroku
- [ ] Created Heroku app
- [ ] Added PostgreSQL (Standard for 861k rows)
- [ ] Added Redis
- [ ] Set all environment variables
- [ ] Pushed code to Heroku
- [ ] Scaled web=1 and worker=1
- [ ] Tested health endpoint
- [ ] Tested creating a product
- [ ] Tested CSV upload
- [ ] Checked logs for errors
- [ ] Documented app URL

---

## 🎉 Success!

Your app should now be live at:
`https://your-app-name.herokuapp.com`

**Share your URL in the assignment submission!**

---

## 📧 Assignment Submission

Include in your email:

1. **GitHub Repository URL**
2. **Heroku App URL** (live deployment)
3. **Screenshots**:
   - CSV import in progress
   - Product management page
   - Webhook configuration
4. **Brief description** of tech stack used
5. **(Optional)** AI tool conversation logs

---

Need help? Check:
- Heroku Dev Center: https://devcenter.heroku.com/
- Heroku Support: https://help.heroku.com/

