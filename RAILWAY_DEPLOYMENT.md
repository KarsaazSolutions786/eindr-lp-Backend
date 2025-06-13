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
- `DATABASE_URL` - PostgreSQL connection string (format: `postgres://user:pass@host:port/db`)

**Manual Variables (if needed):**
1. Go to your service settings
2. Click "**Variables**" tab
3. Add any custom environment variables

**Example Variables:**
```
DATABASE_URL=postgres://user:pass@host:port/db  # Auto-provided by Railway
PORT=8000  # Auto-provided by Railway
CORS_ORIGINS=["https://your-frontend-domain.com"]  # Optional
```

### 5. **Deploy Configuration**

Your project already includes:

**📄 railway.json**
```json
{
  "deploy": {
    "startCommand": "python3 start.py",
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

Your app automatically handles Railway's `DATABASE_URL`:
```python
# Railway provides: postgres://user:pass@host:port/db
# App converts to: postgresql+psycopg://user:pass@host:port/db
```

### Application Settings

- **Port**: Railway sets `$PORT` environment variable
- **Host**: `0.0.0.0` (configured in your app)
- **Health Check**: `/health` endpoint with database status
- **Auto-restart**: Configured for failures

## 🚨 Troubleshooting

### Common Issues:

1. **Database Connection Errors**
   ```
   sqlalchemy.engine.base.py: Failed to connect to database
   ```
   
   **Solutions:**
   - ✅ Ensure PostgreSQL service is running in Railway
   - ✅ Check that `DATABASE_URL` environment variable is set
   - ✅ Verify Railway PostgreSQL service is healthy
   - ✅ Check Railway logs for database initialization

2. **PORT Environment Variable Issues**
   ```
   Error: Invalid value for '--port': '$PORT' is not a valid integer
   ```
   
   **Solution:** ✅ **FIXED** - Now using `start.py` with proper PORT handling

3. **Build Failures**
   - Check Railway build logs
   - Ensure `requirements.txt` has correct dependencies
   - Verify Dockerfile syntax

4. **Health Check Failures**
   - The app now includes database status in health checks
   - `/health` endpoint returns "degraded" if database is unavailable
   - App can start even if database connection fails initially

### Railway-Specific Database Setup:

1. **Check Database Service**: Ensure PostgreSQL service is running
2. **Environment Variables**: Verify `DATABASE_URL` is automatically set
3. **Connection Format**: Railway uses `postgres://` which app converts to `postgresql+psycopg://`
4. **Database Logs**: Check Railway PostgreSQL service logs

### Debug Commands:

```bash
# View service logs
railway logs

# View environment variables  
railway variables

# Connect to database
railway connect postgres

# Check database status
curl https://your-app.railway.app/health
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

**Enhanced Health Monitoring:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T12:00:00Z",
  "database_status": "connected"
}
```

## 🎉 Success!

Once deployed, your API will be available at:
- **Railway URL**: `https://your-app-name-production.up.railway.app`
- **Health Check**: `/health` (includes database status)
- **API Documentation**: `/docs`
- **Submit Email**: `POST /submit-email`

Your PostgreSQL database will be persistent and managed by Railway with automatic backups.

## 🛠️ Railway PostgreSQL Connection Details

Railway automatically provides these environment variables:
- `DATABASE_URL` - Full connection string
- `POSTGRES_DB` - Database name  
- `POSTGRES_HOST` - Database host
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_PORT` - Database port (5432)
- `POSTGRES_USER` - Database username

Your app uses `DATABASE_URL` directly and handles the format conversion automatically.

---

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app)
- [Railway PostgreSQL Guide](https://docs.railway.app/databases/postgresql)
- [Railway Environment Variables](https://docs.railway.app/deploy/environment-variables)

Happy deploying! 🚀 