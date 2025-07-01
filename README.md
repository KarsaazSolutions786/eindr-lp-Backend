# 🌍 Eindr Email Capture + Multi-Language Label Management API

**Version 2.0.0** - Now with Multi-Language Label Management System!

A FastAPI backend service for capturing email addresses from landing pages with comprehensive multi-language label management capabilities.

## ✨ Features

### Original Email Capture Features
- 📧 **Email Collection**: Capture and store email addresses from landing pages
- 🔐 **Admin Dashboard**: Protected endpoints for viewing email statistics
- 🗃️ **PostgreSQL Database**: Reliable data storage with async support
- 🚀 **Railway Deployment**: Ready for cloud deployment
- 🛡️ **Input Validation**: Email format validation and duplicate handling
- 📊 **Statistics API**: Track email submission metrics

### 🆕 New Multi-Language Label Management Features
- 🌍 **Language Management**: Create and manage multiple languages
- 🏷️ **Label Organization**: Group labels by categories (home, navigation, forms, etc.)
- 📝 **Translation Management**: Store and manage translations for each label
- ✅ **Data Validation**: Comprehensive validation before inserting translations
- 🔍 **Query System**: Retrieve labels by language, group, or specific combinations
- 🔒 **Admin Protection**: Secure endpoints for managing translations
- 📡 **RESTful API**: Complete CRUD operations for all label components

## 🚀 Quick Start

### 1. Set Up the Database

```bash
# Install dependencies
pip3 install -r requirements.txt

# Set up sample data (optional)
python3 setup_sample_data.py
```

### 2. Start the API

```bash
# Start the FastAPI server
python3 start.py
```

The API will be available at:
- **Main API**: `http://localhost:8004`
- **Interactive Docs**: `http://localhost:8004/docs`
- **Alternative Docs**: `http://localhost:8004/redoc`

### 3. Test the API

#### Email Capture (Original Feature)
```bash
# Submit an email
curl -X POST "http://localhost:8004/submit-email" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

#### Multi-Language Labels (New Feature)
```bash
# Get all languages
curl "http://localhost:8004/api/languages"

# Get labels for English
curl "http://localhost:8004/api/languages/1/labels"

# Validate and insert a new translation (admin required)
curl -X POST "http://localhost:8004/api/labels/insert-with-validation" \
     -H "Content-Type: application/json" \
     -u "admin@karsaaz.com:Admin123" \
     -d '{
       "language_id": 1,
       "label_group_id": 1,
       "label_code_id": 1,
       "label_text": "Welcome to our website!"
     }'
```

## 📡 API Endpoints

### Email Capture Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Health check | No |
| GET | `/health` | Detailed health status | No |
| POST | `/submit-email` | Submit email address | No |
| GET | `/stats` | Email statistics | Yes |
| GET | `/emails` | List all emails | Yes |

### Multi-Language Label Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/languages` | List all languages | No |
| POST | `/api/languages` | Create new language | Yes |
| GET | `/api/languages/{id}` | Get specific language | No |
| PUT | `/api/languages/{id}` | Update language | Yes |
| GET | `/api/languages/{id}/labels` | Get all labels for language | No |
| GET | `/api/label-groups` | List all label groups | No |
| POST | `/api/label-groups` | Create new label group | Yes |
| POST | `/api/label-codes` | Create new label code | Yes |
| POST | `/api/labels/validate` | Validate before insertion | Yes |
| POST | `/api/language-labels` | Create translation | Yes |
| GET | `/api/language-labels/{lang_id}/{label_id}` | Get specific translation | No |
| POST | `/api/labels/insert-with-validation` | Complete workflow | Yes |

## 🔒 Authentication

Admin endpoints require HTTP Basic Authentication:
- **Username**: `admin@karsaaz.com`
- **Password**: `Admin123`

Example:
```bash
curl -u "admin@karsaaz.com:Admin123" "http://localhost:8004/api/language-labels"
```

## 📊 Database Schema

### Email Capture Tables
- `emails` - Stores email addresses with timestamps

### Multi-Language Label Tables
- `languages` - Supported languages (English, Spanish, etc.)
- `label_groups` - Categories for organizing labels (home, navigation, etc.)
- `label_codes` - Unique identifiers for each translatable element
- `language_label` - Actual translations linking languages to label codes

## 🌍 Usage Examples

### Frontend Integration

#### JavaScript/React
```javascript
// Fetch labels for current language
const loadLabels = async (languageId) => {
  const response = await fetch(`/api/languages/${languageId}/labels`);
  const data = await response.json();
  return data.labels;
};

// Usage
const labels = await loadLabels(1); // English
console.log(labels.home.text_welcome); // "Welcome to our website!"
console.log(labels.navigation.menu_about); // "About"
```

#### Python Backend
```python
import requests

# Get labels for Spanish
response = requests.get('http://localhost:8004/api/languages/2/labels')
labels = response.json()['labels']

# Access specific label
welcome_text = labels['home']['text_welcome']  # "¡Bienvenido a nuestro sitio web!"
```

### Adding New Translations

1. **Validate the data**:
```bash
curl -X POST "http://localhost:8004/api/labels/validate" \
     -H "Content-Type: application/json" \
     -u "admin@karsaaz.com:Admin123" \
     -d '{
       "language_id": 1,
       "label_group_id": 1,
       "label_code_id": 1,
       "label_text": "Hello World!"
     }'
```

2. **Insert the translation**:
```bash
curl -X POST "http://localhost:8004/api/language-labels" \
     -H "Content-Type: application/json" \
     -u "admin@karsaaz.com:Admin123" \
     -d '{
       "language_id": 1,
       "label_id": 1,
       "label_text": "Hello World!"
     }'
```

3. **Or use the combined workflow**:
```bash
curl -X POST "http://localhost:8004/api/labels/insert-with-validation" \
     -H "Content-Type: application/json" \
     -u "admin@karsaaz.com:Admin123" \
     -d '{
       "language_id": 1,
       "label_group_id": 1,
       "label_code_id": 1,
       "label_text": "Hello World!"
     }'
```

## 🚀 Railway Deployment

This project is configured for easy deployment on Railway:

1. **Push to GitHub**
2. **Connect Railway to your repository**
3. **Add PostgreSQL database service**
4. **Deploy** - Railway handles the rest!

The app includes:
- ✅ Proper `Dockerfile` for containerization
- ✅ Railway-compatible `start.py` script
- ✅ Automatic database URL handling
- ✅ Environment variable configuration
- ✅ Health check endpoints

See `RAILWAY_DEPLOYMENT.md` for detailed deployment instructions.

## 📚 Documentation

- **Multi-Language System**: See `MULTI_LANGUAGE_LABELS.md` for comprehensive documentation
- **API Reference**: Visit `/docs` endpoint when running the server
- **Deployment Guide**: See `RAILWAY_DEPLOYMENT.md`
- **Sample Data**: Run `python3 setup_sample_data.py` to populate with example data

## 🛠️ Development

### Local Development Setup

1. **Clone the repository**
2. **Install dependencies**: `pip3 install -r requirements.txt`
3. **Set up local PostgreSQL** (optional - uses Railway DB by default)
4. **Run setup script**: `python3 setup_sample_data.py`
5. **Start the server**: `python3 start.py`

### Project Structure

```
eindr(lp)Backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── database_psycopg.py    # Database models and connection
│   ├── models.py              # Pydantic models
│   ├── services.py            # Business logic
│   ├── main_postgresql.py     # FastAPI application
│   └── main.py                # Alternative main file
├── setup_sample_data.py       # Sample data creation script
├── start.py                   # Railway-compatible startup script
├── Dockerfile                 # Container configuration
├── railway.json              # Railway deployment config
├── requirements.txt          # Python dependencies
├── MULTI_LANGUAGE_LABELS.md  # Label system documentation
├── RAILWAY_DEPLOYMENT.md     # Deployment guide
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (auto-provided by Railway)
- `PORT` - Server port (auto-provided by Railway, defaults to 8004)
- `CORS_ORIGINS` - Allowed CORS origins
- `ENVIRONMENT` - Environment setting (development/production)

### Local Development

Create a `.env` file (use `env.template` as reference):
```bash
DATABASE_URL=postgresql+psycopg://postgres:admin123@localhost/eindr_lp
API_PORT=8004
CORS_ORIGINS=["*"]
```

## 🚨 Error Handling

The API includes comprehensive error handling:

- **Email Validation**: Checks for valid email format and duplicates
- **Translation Validation**: Ensures all referenced entities exist
- **Database Errors**: Graceful handling of connection and constraint issues
- **Authentication Errors**: Clear messages for auth failures
- **Input Validation**: Pydantic validation for all request bodies

## 📈 Monitoring

### Health Checks

- `GET /health` - Returns system status and database connectivity
- Includes database status in health check response
- Compatible with Railway health monitoring

### Logging

The application includes structured logging:
- Request/response logging
- Database operation logging
- Error tracking with stack traces
- Admin action auditing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly (both email capture and label management features)
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Related Projects

- **Frontend**: Connect your frontend application to consume the labels API
- **Admin Dashboard**: Build a web interface for managing translations
- **Migration Tools**: Create scripts to import existing translation files

---

**Version History:**
- **v2.0.0**: Added Multi-Language Label Management System
- **v1.0.0**: Initial Email Capture API

For detailed information about the multi-language features, see `MULTI_LANGUAGE_LABELS.md`. 