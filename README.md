# Eindr Email Capture Backend

A FastAPI backend service for capturing email addresses from the Eindr landing page. Built with PostgreSQL, async support, and ready for Railway deployment.

## Features

- 🚀 **FastAPI**: Modern, fast Python web framework
- 🗃️ **PostgreSQL**: Secure email storage with UUID primary keys
- 🔒 **Security**: HTTPS enforcement, input validation, and secure database handling
- 🌐 **CORS**: Configured for frontend integration
- 📊 **Monitoring**: Health checks and basic analytics
- 🚢 **Railway Ready**: One-click deployment configuration

## API Endpoints

### `POST /submit-email`
Submit an email address for registration.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email successfully registered. We'll keep you updated!",
  "email_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0"
}
```

### `GET /stats`
Get basic statistics about email submissions.

**Response:**
```json
{
  "total_emails": 150,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## Database Schema

### `emails` table
```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_emails_email ON emails(email);
CREATE INDEX idx_emails_created_at ON emails(created_at);
```

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- pip or poetry

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eindr-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   ```bash
   # Create database
   createdb eindr_db
   
   # Or using psql
   psql -c "CREATE DATABASE eindr_db;"
   ```

4. **Environment variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://username:password@localhost/eindr_lp
   POSTGRES_USER=username
   POSTGRES_PASSWORD=password
   POSTGRES_DB=eindr_db
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:3000,https://eindr.com
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## Deployment

### Railway Deployment

1. **Connect your repository to Railway**
   - Fork/clone this repository
   - Connect to Railway via GitHub

2. **Add PostgreSQL service**
   - In Railway dashboard, add a PostgreSQL service
   - Note the connection details

3. **Set environment variables**
   Railway will automatically set `DATABASE_URL`. Add these additional variables:
   ```
   ENVIRONMENT=production
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Deploy**
   - Push to your connected branch
   - Railway will automatically build and deploy

### Manual Docker Deployment

```bash
# Build the image
docker build -t eindr-backend .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=your_postgres_url \
  -e ENVIRONMENT=production \
  eindr-backend
```

## Frontend Integration

### Example JavaScript fetch request:

```javascript
const submitEmail = async (email) => {
  try {
    const response = await fetch('https://your-api-url.com/submit-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Email submitted successfully!');
    } else {
      console.error('Error:', result.message);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

### Example React form:

```jsx
import { useState } from 'react';

function EmailCapture() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    
    try {
      const response = await fetch('/submit-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      
      const result = await response.json();
      
      if (result.success) {
        setStatus('success');
        setEmail('');
      } else {
        setStatus('error');
      }
    } catch (error) {
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
        required
      />
      <button type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Submitting...' : 'Submit'}
      </button>
      {status === 'success' && <p>Thank you! We'll keep you updated.</p>}
      {status === 'error' && <p>Something went wrong. Please try again.</p>}
    </form>
  );
}
```

## Security Features

- **Email Validation**: Robust email format validation using Pydantic
- **Duplicate Prevention**: Unique constraint prevents duplicate emails
- **HTTPS Enforcement**: Automatic HTTPS redirect in production
- **Input Sanitization**: All inputs are validated and sanitized
- **Rate Limiting Ready**: Structure supports adding rate limiting middleware
- **Secure Headers**: Production-ready security configurations

## Monitoring & Logging

- **Structured Logging**: JSON formatted logs for production monitoring
- **Health Checks**: Built-in health check endpoints
- **Error Tracking**: Comprehensive error handling and logging
- **Database Monitoring**: Connection pooling and query logging

## Development

### Adding Features

The codebase is structured for easy extension:

- `app/models.py`: Add new Pydantic models
- `app/services.py`: Add new business logic
- `app/main.py`: Add new API endpoints
- `app/database.py`: Add new database models

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please open a GitHub issue or contact the development team. 