# Railway Deployment Guide - Flask Backend

This guide covers deploying the Frames Flask backend to Railway with PostgreSQL database.

## Why Railway over Vercel Functions?

### Railway Advantages for This Project:
✅ **Full Server Environment** - Traditional Flask app runs as-is
✅ **Persistent Storage** - File uploads stored directly on disk
✅ **PostgreSQL Database** - Built-in database service with automatic backups
✅ **No Code Changes** - Deploy existing Flask app without refactoring
✅ **WebSocket Support** - If you need real-time features later
✅ **Longer Timeouts** - No 10-second execution limit
✅ **Better for Monoliths** - Designed for traditional web apps

### Vercel Functions Limitations:
❌ **Serverless Only** - Requires significant refactoring for Flask
❌ **No Persistent Storage** - File uploads need external S3/Cloudinary
❌ **50MB Deploy Limit** - With dependencies, this gets tight
❌ **10-Second Timeout** - Problems for image processing/3D generation
❌ **Stateless** - No in-memory caching or session storage
❌ **Cold Starts** - First requests are slower

**Verdict**: For a Flask app with file uploads, PostgreSQL, and image processing, **Railway is significantly better**.

---

## Prerequisites

- GitHub/GitLab/Bitbucket account
- Railway account (free tier available): https://railway.app
- Your Vercel frontend URL (for CORS configuration)

---

## Quick Deployment (Recommended)

### Step 1: Prepare Your Repository

Ensure your backend code is pushed to GitHub:

```bash
git add backend/
git commit -m "Add Railway deployment config"
git push
```

### Step 2: Deploy to Railway

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/new
   - Click "Deploy from GitHub repo"
   - Authorize Railway to access your repository

2. **Select Your Repository**
   - Choose: `InspiredReality/frames`
   - Railway will detect it's a Python project

3. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway automatically creates `DATABASE_URL` environment variable

4. **Configure Root Directory**
   - In project settings, set **Root Directory**: `backend`
   - This tells Railway to deploy only the backend folder

5. **Set Environment Variables**

   Go to your service → Variables tab and add:

   ```bash
   # Required
   SECRET_KEY=your-random-secret-key-generate-new-one
   JWT_SECRET_KEY=your-jwt-secret-key-generate-new-one
   FLASK_ENV=production

   # CORS - Add your Vercel URL
   CORS_ORIGINS=https://your-app.vercel.app

   # Optional (Railway sets these by default)
   UPLOAD_FOLDER=uploads
   MAX_CONTENT_LENGTH=16777216
   JWT_ACCESS_TOKEN_EXPIRES=3600
   ```

   **Generate Secure Keys:**
   ```bash
   # In your terminal:
   python -c "import secrets; print(secrets.token_hex(32))"
   # Copy output for SECRET_KEY

   python -c "import secrets; print(secrets.token_hex(32))"
   # Copy output for JWT_SECRET_KEY
   ```

6. **Deploy!**
   - Click "Deploy" or Railway auto-deploys on push
   - Wait 2-3 minutes for build to complete
   - Railway will provide a URL like: `https://your-app.up.railway.app`

### Step 3: Update Frontend Environment Variables

Update your Vercel project's environment variables:

```bash
VITE_API_URL=https://your-app.up.railway.app/api
```

Redeploy your Vercel frontend for changes to take effect.

---

## Alternative: CLI Deployment

### Install Railway CLI

```bash
# macOS
brew install railway

# npm
npm install -g @railway/cli

# Or download: https://docs.railway.app/develop/cli
```

### Login and Deploy

```bash
# Login
railway login

# Navigate to backend folder
cd backend

# Initialize project (first time only)
railway init

# Link to existing project or create new
railway link

# Add PostgreSQL (first time only)
railway add --database postgresql

# Set environment variables
railway variables set SECRET_KEY="your-secret-key"
railway variables set JWT_SECRET_KEY="your-jwt-secret"
railway variables set FLASK_ENV="production"
railway variables set CORS_ORIGINS="https://your-app.vercel.app"

# Deploy
railway up

# View logs
railway logs
```

---

## Database Setup

Railway automatically creates a PostgreSQL database with these variables:

- `DATABASE_URL` - Full connection string (auto-injected)
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - Individual components

Your Flask app automatically uses `DATABASE_URL` from the environment (see `backend/app/config.py:16-18`).

### Run Migrations (First Deployment)

If you need to run database migrations:

```bash
# Option 1: Railway CLI
railway run flask db upgrade

# Option 2: Railway Dashboard
# Go to your service → Settings → "Run Command"
# Enter: flask db upgrade
```

---

## File Uploads & Storage

### Current Setup
The app saves uploads to the `uploads/` folder on Railway's persistent disk.

**Railway Storage:**
- ✅ Free tier: 1GB persistent storage (more than enough for pictures)
- ✅ Files persist across deployments
- ✅ Automatic backups with paid plans

### For Production Scale (Optional)

If you expect thousands of images, consider external storage:

1. **Cloudinary** (Recommended for images)
   - Free tier: 25GB storage, 25GB bandwidth
   - Image transformations, CDN, optimization
   - Add `cloudinary` to requirements.txt

2. **AWS S3** or **Railway Volumes**
   - S3: Pay-as-you-go, unlimited storage
   - Railway Volumes: Larger persistent storage

For now, **Railway's built-in storage is perfect** for getting started.

---

## Updating CORS for Production

Your backend's CORS is configured in `backend/app/__init__.py:47-58`.

### Add Multiple Origins

Update Railway environment variable:

```bash
CORS_ORIGINS=https://your-app.vercel.app,https://custom-domain.com,https://staging.vercel.app
```

The app automatically splits by comma and allows all listed origins.

### Security Best Practices

1. **Never use `*` in production** - Always specify exact domains
2. **Use HTTPS only** - No `http://` URLs in CORS_ORIGINS
3. **Rotate secrets** - Change SECRET_KEY and JWT_SECRET_KEY regularly
4. **Enable Railway auth** - Use Railway's built-in authentication for sensitive endpoints

---

## Monitoring & Debugging

### View Logs

**Railway Dashboard:**
1. Go to your service
2. Click "Deployments" tab
3. Click latest deployment
4. View real-time logs

**Railway CLI:**
```bash
railway logs
railway logs -f  # Follow logs in real-time
```

### Health Check

Railway uses the `/api/health` endpoint to monitor your app:

```bash
curl https://your-app.up.railway.app/api/health
# Should return: {"status": "healthy", "message": "Frames API is running"}
```

### Common Issues

**Issue: "Application Error" or 503**
- **Fix**: Check logs for Python errors
- **Fix**: Ensure `DATABASE_URL` is set (PostgreSQL added)
- **Fix**: Verify `requirements.txt` has all dependencies

**Issue: CORS errors in frontend**
- **Fix**: Ensure `CORS_ORIGINS` includes your exact Vercel URL
- **Fix**: Check no trailing slashes: `https://app.vercel.app` not `https://app.vercel.app/`
- **Fix**: Verify frontend uses `https://` not `http://`

**Issue: Database connection errors**
- **Fix**: Ensure PostgreSQL database is added to project
- **Fix**: Run migrations: `railway run flask db upgrade`
- **Fix**: Check `DATABASE_URL` is set in environment variables

**Issue: File uploads failing**
- **Fix**: Check `UPLOAD_FOLDER` permissions (Railway handles this automatically)
- **Fix**: Verify `MAX_CONTENT_LENGTH` is set (default: 16MB)
- **Fix**: Ensure uploads/ folder is created (happens automatically on boot)

---

## Deployment Checklist

- [ ] Railway account created
- [ ] GitHub repository connected
- [ ] PostgreSQL database added
- [ ] Root directory set to `backend`
- [ ] Environment variables configured:
  - [ ] `SECRET_KEY` (random, secure)
  - [ ] `JWT_SECRET_KEY` (random, secure)
  - [ ] `FLASK_ENV=production`
  - [ ] `CORS_ORIGINS` (Vercel URL)
- [ ] Backend deployed successfully
- [ ] Health check returns 200: `/api/health`
- [ ] Database migrations run (if needed)
- [ ] Frontend `VITE_API_URL` updated with Railway URL
- [ ] Frontend redeployed to Vercel
- [ ] Test authentication flow works
- [ ] Test file upload works
- [ ] Test CORS (frontend → backend requests)

---

## Custom Domain (Optional)

### Add Custom Domain to Railway

1. Go to your service → Settings → Networking
2. Click "Add Custom Domain"
3. Enter your domain (e.g., `api.yourapp.com`)
4. Add CNAME record to your DNS:
   ```
   CNAME api.yourapp.com → your-app.up.railway.app
   ```
5. Wait for SSL certificate (automatic, ~5 minutes)

### Update Environment Variables

```bash
# Railway
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com

# Vercel frontend
VITE_API_URL=https://api.yourapp.com/api
```

---

## Cost Estimates

### Railway Pricing (as of 2024)

**Free Tier (Hobby Plan):**
- $5 credit/month (enough for small projects)
- 1GB persistent storage
- 512MB RAM per service
- Automatic sleep after inactivity

**Pro Plan:**
- $20/month base + usage
- 100GB storage included
- Better performance
- No sleep
- Team collaboration

**Typical Usage for This Project:**
- Backend: ~$3-5/month (with database)
- PostgreSQL: Included in compute cost
- **Total**: ~$3-5/month (within free tier initially)

### Cost Comparison

| Platform | Backend | Database | Storage | Total/mo |
|----------|---------|----------|---------|----------|
| **Railway** | $3-5 | Included | 1GB free | **$3-5** |
| Vercel Functions | $0-20 | External | External | **$10-30** |
| Heroku | $7 | $9 | External | **$16+** |
| Render | $7 | Free (90 days) | External | **$7+** |

**Railway is the most cost-effective** for full-stack Flask apps.

---

## Scaling & Performance

### Horizontal Scaling

Railway supports horizontal scaling (multiple instances):

```bash
# In Railway dashboard: Settings → Scale
# Increase replicas: 1 → 2 (for high availability)
```

**Note**: With file uploads, ensure you migrate to S3/Cloudinary before scaling horizontally.

### Database Performance

- **Connection Pooling**: Already configured in SQLAlchemy
- **Indexes**: Add indexes to frequently queried fields
- **Monitoring**: Use Railway's built-in metrics

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Update Vercel frontend with Railway API URL
3. 🔄 Test full authentication flow
4. 🔄 Test picture/wall uploads
5. 🔄 Set up monitoring (Railway Metrics)
6. 🔄 Configure custom domain (optional)
7. 🔄 Set up automated backups (Railway Pro)

---

## Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Flask Deployment**: https://flask.palletsprojects.com/en/latest/deploying/
- **PostgreSQL on Railway**: https://docs.railway.app/databases/postgresql
- **Frames API Docs**: See backend/README.md (if exists) or main README.md

---

## Support

**Issues with Railway deployment?**
1. Check deployment logs in Railway dashboard
2. Review this guide's "Common Issues" section
3. Test `/api/health` endpoint
4. Verify environment variables match `.env.production` template

**Need help?**
- Railway Support: https://help.railway.app
- Project Issues: https://github.com/InspiredReality/frames/issues
