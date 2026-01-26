# Deploying to Vercel

This guide will help you deploy the Frames frontend to Vercel.

## Overview

The Frames application consists of:
- **Frontend**: Vue.js + Vite (deployed to Vercel)
- **Backend**: Flask + PostgreSQL (needs separate deployment)

This guide covers deploying the frontend to Vercel. The backend should be deployed separately to a platform that supports Python applications (e.g., Railway, Render, Heroku, or a VPS).

## Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. [Vercel CLI](https://vercel.com/cli) installed (optional, for CLI deployment)
3. Your backend API deployed and accessible via HTTPS

## Deployment Options

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Connect your repository to Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your Git repository (GitHub, GitLab, or Bitbucket)
   - Select the repository containing this project

2. **Configure the project**:
   - Vercel will auto-detect the `vercel.json` configuration
   - Project name: Choose a name (e.g., `frames-frontend`)
   - Framework Preset: **Other** (we've configured it manually)

3. **Set Environment Variables**:
   Click "Environment Variables" and add:
   ```
   VITE_API_URL=https://your-backend-api.com/api
   VITE_UNITY_BUILD_PATH=/unity
   ```

   Replace `https://your-backend-api.com/api` with your actual backend API URL.

4. **Deploy**:
   - Click "Deploy"
   - Wait for the build to complete
   - Your frontend will be available at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from the project root**:
   ```bash
   vercel
   ```

   Follow the prompts:
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N** (first time)
   - What's your project's name? Enter a name
   - In which directory is your code located? `./`

4. **Set environment variables**:
   ```bash
   vercel env add VITE_API_URL
   # Enter: https://your-backend-api.com/api

   vercel env add VITE_UNITY_BUILD_PATH
   # Enter: /unity
   ```

5. **Deploy to production**:
   ```bash
   vercel --prod
   ```

## Configuration Details

### vercel.json

The `vercel.json` file at the project root configures:

- **buildCommand**: Installs dependencies and builds the Vue app
- **outputDirectory**: Points to `frontend/dist` where Vite outputs the build
- **rewrites**: Enables SPA routing by redirecting all routes to `index.html`
- **headers**: Sets cache headers for optimal performance

### Environment Variables

The following environment variables must be set in Vercel:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://api.yourapp.com/api` |
| `VITE_UNITY_BUILD_PATH` | Path to Unity WebGL build | `/unity` |

**Important**: Environment variables prefixed with `VITE_` are embedded into the frontend build at build time.

## Backend Deployment

The backend Flask application needs to be deployed separately. Recommended platforms:

### Railway (Recommended)
1. Visit [railway.app](https://railway.app/)
2. Create a new project from your GitHub repo
3. Set root directory to `backend`
4. Add PostgreSQL database
5. Set environment variables (see backend/.env.example)

### Render
1. Visit [render.com](https://render.com/)
2. Create a new Web Service
3. Connect your repository
4. Set root directory to `backend`
5. Add PostgreSQL database
6. Set environment variables

### Other Options
- **Heroku**: Good for small projects (has free tier limitations)
- **DigitalOcean App Platform**: Simple deployment with managed databases
- **AWS Elastic Beanstalk**: For more complex, scalable deployments
- **VPS** (DigitalOcean, Linode, etc.): Full control, requires manual setup

## Post-Deployment

### 1. Update CORS Settings

In your backend's configuration (`backend/app/config.py` or `.env`), add your Vercel domain to allowed CORS origins:

```python
CORS_ORIGINS=https://your-project.vercel.app,https://your-custom-domain.com
```

### 2. Test the Deployment

1. Visit your Vercel URL
2. Try registering/logging in
3. Test uploading pictures and walls
4. Verify API requests are working (check browser console)

### 3. Custom Domain (Optional)

1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. Update CORS settings in backend to include the custom domain

## Troubleshooting

### Build Fails

**Error: "npm install failed"**
- Check that `frontend/package.json` is valid
- Verify all dependencies are listed

**Error: "Build command failed"**
- Test the build locally: `cd frontend && npm run build`
- Check build logs in Vercel dashboard for specific errors

### API Calls Fail

**Error: "Network Error" or CORS errors**
- Verify `VITE_API_URL` is set correctly in Vercel
- Check that backend CORS settings include your Vercel domain
- Ensure backend is accessible via HTTPS

**Error: "API returns 404"**
- Verify the API URL includes `/api` at the end
- Check that your backend is running and accessible

### Environment Variables Not Working

- Remember: Vite environment variables must be prefixed with `VITE_`
- Changes to environment variables require a new deployment
- Verify variables are set for the correct environment (Production/Preview/Development)

## Continuous Deployment

Vercel automatically deploys:
- **Production**: Commits to your main/master branch
- **Preview**: Pull requests and other branches

To disable auto-deployment:
1. Go to Project Settings → Git
2. Configure deployment branches

## Monitoring

Vercel provides built-in analytics:
- **Deployments**: View all deployments and their status
- **Analytics**: Track page views and Web Vitals
- **Logs**: Real-time function and build logs

Access these in your Vercel project dashboard.

## Local Development with Production API

To test locally with your production backend:

1. Create `frontend/.env.local`:
   ```
   VITE_API_URL=https://your-backend-api.com/api
   ```

2. Run dev server:
   ```bash
   cd frontend
   npm run dev
   ```

## Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Vue.js Deployment Guide](https://vuejs.org/guide/best-practices/production-deployment.html)

## Support

If you encounter issues:
1. Check the [Vercel Documentation](https://vercel.com/docs)
2. Review build logs in the Vercel dashboard
3. Test the build locally: `cd frontend && npm run build && npm run preview`
