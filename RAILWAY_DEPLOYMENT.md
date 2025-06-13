# 🚀 Railway Deployment Guide for Eindr Email Capture API

This guide will walk you through deploying your Eindr Email Capture API to Railway with PostgreSQL database.

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Local Testing**: Ensure your API works locally with PostgreSQL

## 🚂 Step-by-Step Deployment Process

### 1. **Prepare Your Railway Account**

1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Connect your GitHub account

### 2. **Create New Railway Project**

1. Click "**New Project**"
2. Select "**Deploy from GitHub repo**"
3. Choose your repository: `eindr(lp)Backend`
4. Railway will automatically detect your `Dockerfile`

### 3. **Add PostgreSQL Database**

1. In your Railway project dashboard, click "**+ New**"
2. Select "**Database**" → "**PostgreSQL**"
3. Railway will create a PostgreSQL instance and provide connection details
4. **Important**: Railway automatically sets the `DATABASE_URL` environment variable

### 4. **Configure Environment Variables**

Railway automatically provides:
- `PORT` - The port your app should listen on
- `DATABASE_URL` - PostgreSQL connection string

**Manual Variables (if needed):**
1. Go to your service settings
2. Click "**Variables**" tab
3. Add any custom environment variables

**Example Variables:**
```
DATABASE_URL=postgresql+psycopg://user:pass@host:port/db  # Auto-provided
PORT=8000  # Auto-provided
CORS_ORIGINS=["https://your-frontend-domain.com"]  # Optional
```

### 5. **Deploy Configuration**

Your project already includes:

**📄 railway.json**
```json
{
  "deploy": {
    "startCommand": "uvicorn app.main_postgresql:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

**🐳 Dockerfile** - Optimized for Railway deployment

### 6. **Deployment Steps**

1. **Push to GitHub**: Ensure all your code is pushed to GitHub
2. **Automatic Deployment**: Railway automatically deploys when you push to GitHub
3. **Monitor Logs**: Watch the deployment logs in Railway dashboard
4. **Wait for Success**: Deployment takes 2-5 minutes

### 7. **Verify Deployment**

Once deployed, Railway provides a URL like: `https://your-app-name-production.up.railway.app`

**Test your endpoints:**
```bash
# Health check
curl https://your-app-name-production.up.railway.app/health

# Submit email
curl -X POST https://your-app-name-production.up.railway.app/submit-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# View stats
curl https://your-app-name-production.up.railway.app/stats
```

## 🔧 Configuration Details

### Database Connection

Railway automatically configures the PostgreSQL connection:
- **Host**: Provided by Railway
- **Port**: 5432 (default)
- **Database**: Auto-generated name
- **User/Password**: Auto-generated
- **SSL**: Enabled by default

Your `app/database_psycopg.py` reads the `DATABASE_URL` environment variable:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://...")
```

### Application Settings

- **Port**: Railway sets `$PORT` environment variable
- **Host**: `0.0.0.0` (configured in your app)
- **Health Check**: `/health` endpoint
- **Auto-restart**: Configured for failures

## 🚨 Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check Railway build logs
   - Ensure `requirements.txt` has correct dependencies
   - Verify Dockerfile syntax

2. **Database Connection Issues**
   - Ensure PostgreSQL service is running
   - Check if `DATABASE_URL` is set correctly
   - Verify psycopg dependencies are installed

3. **Port Issues**
   - Railway sets `$PORT` automatically
   - Ensure your app uses `$PORT` environment variable

4. **Health Check Failures**
   - Verify `/health` endpoint works locally
   - Check if app starts correctly

### Debug Commands:

```bash
# View service logs
railway logs

# View environment variables
railway variables

# Connect to database
railway connect postgres
```

## 🔄 Redeployment

**Automatic**: Every push to your GitHub main branch triggers redeployment

**Manual**: 
1. Go to Railway dashboard
2. Click "**Redeploy**" button

## 🌐 Custom Domain (Optional)

1. Go to your service in Railway
2. Click "**Settings**" → "**Domains**"
3. Add your custom domain
4. Configure DNS records as instructed

## 📊 Monitoring

Railway provides:
- **Real-time logs**
- **Metrics dashboard**
- **Usage analytics**
- **Uptime monitoring**

## 🎉 Success!

Once deployed, your API will be available at:
- **Railway URL**: `https://your-app-name-production.up.railway.app`
- **Health Check**: `/health`
- **API Documentation**: `/docs`
- **Submit Email**: `POST /submit-email`

Your PostgreSQL database will be persistent and managed by Railway with automatic backups.

---

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app)
- [Railway PostgreSQL Guide](https://docs.railway.app/databases/postgresql)
- [Railway Environment Variables](https://docs.railway.app/deploy/environment-variables)

Happy deploying! 🚀 