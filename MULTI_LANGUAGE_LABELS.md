# 🌍 Multi-Language Label Management System

This document describes the multi-language label management system integrated into the Eindr Email Capture API.

## 📋 Overview

The multi-language label management system allows you to:

- **Manage Languages**: Create and maintain supported languages
- **Organize Labels**: Group related labels using label groups
- **Define Label Codes**: Create unique identifiers for each translatable element
- **Store Translations**: Manage translations for each label in multiple languages
- **Validate Data**: Ensure data integrity before inserting translations

## 🗄️ Database Schema

### Tables Structure

```sql
-- Languages table
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,     -- e.g., "English", "Spanish"
    code VARCHAR(10) UNIQUE NOT NULL,      -- e.g., "en", "es"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Label Groups table
CREATE TABLE label_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,     -- e.g., "home", "navigation"
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Label Codes table
CREATE TABLE label_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL,            -- e.g., "text_welcome", "btn_submit"
    description TEXT,
    label_group_id INTEGER REFERENCES label_groups(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(code, label_group_id)          -- Code must be unique within group
);

-- Language Labels table (translations)
CREATE TABLE language_label (
    id SERIAL PRIMARY KEY,
    language_id INTEGER REFERENCES languages(id),
    label_id INTEGER REFERENCES label_codes(id),
    label_text TEXT NOT NULL,             -- The actual translation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(language_id, label_id)         -- One translation per language per label
);
```

## 🚀 Quick Start

### 1. Set Up Sample Data

```bash
# Run the sample data setup script
python3 setup_sample_data.py
```

This creates:
- 5 languages (English, Spanish, French, German, Portuguese)
- 5 label groups (home, navigation, forms, errors, common)
- 18 label codes
- Translations for English, Spanish, and French

### 2. Start the API

```bash
# Start the FastAPI server
python3 start.py
```

### 3. Access the API Documentation

Visit `http://localhost:8004/docs` to see the interactive API documentation.

## 📡 API Endpoints

### Language Management

#### Create Language
```http
POST /api/languages
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "name": "Italian",
    "code": "it",
    "is_active": true
}
```

#### Get All Languages
```http
GET /api/languages?active_only=true
```

#### Get Specific Language
```http
GET /api/languages/1
```

#### Update Language
```http
PUT /api/languages/1
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "name": "English (US)",
    "is_active": true
}
```

### Label Group Management

#### Create Label Group
```http
POST /api/label-groups
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "name": "footer",
    "description": "Footer section labels"
}
```

#### Get All Label Groups
```http
GET /api/label-groups
```

### Label Code Management

#### Create Label Code
```http
POST /api/label-codes
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "code": "text_copyright",
    "description": "Copyright text",
    "label_group_id": 1
}
```

#### Get Label Codes by Group
```http
GET /api/label-groups/1/codes
```

### Translation Management

#### Validate Before Insertion (Step 1 of your SQL process)
```http
POST /api/labels/validate
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "language_id": 1,
    "label_group_id": 2,
    "label_code_id": 3,
    "label_text": "Welcome to our website!"
}
```

**Response:**
```json
{
    "valid": true,
    "language_exists": true,
    "label_group_exists": true,
    "label_code_exists": true,
    "message": "✅ All validation checks passed. Ready to insert label."
}
```

#### Create Translation (Step 2 of your SQL process)
```http
POST /api/language-labels
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "language_id": 1,
    "label_id": 3,
    "label_text": "Welcome to our website!"
}
```

#### Get Translation (Step 3 of your SQL process)
```http
GET /api/language-labels/1/3
```

#### Complete Workflow (All 3 steps combined)
```http
POST /api/labels/insert-with-validation
Authorization: Basic admin@karsaaz.com:Admin123
Content-Type: application/json

{
    "language_id": 1,
    "label_group_id": 2,
    "label_code_id": 3,
    "label_text": "Welcome to our website!"
}
```

**Response:**
```json
{
    "step": "complete",
    "success": true,
    "validation_result": {
        "valid": true,
        "language_exists": true,
        "label_group_exists": true,
        "label_code_exists": true,
        "message": "✅ All validation checks passed. Ready to insert label."
    },
    "created_label": {
        "id": 123,
        "language_id": 1,
        "label_id": 3,
        "label_text": "Welcome to our website!",
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2023-12-01T12:00:00Z"
    },
    "verification_result": {
        "id": 123,
        "language_id": 1,
        "label_id": 3,
        "label_text": "Welcome to our website!",
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2023-12-01T12:00:00Z"
    },
    "message": "✅ Label successfully validated, inserted, and verified!"
}
```

### Query Endpoints

#### Get All Labels for a Language
```http
GET /api/languages/1/labels
```

**Response:**
```json
{
    "language_id": 1,
    "language_name": "English",
    "language_code": "en",
    "labels": {
        "home": {
            "text_welcome": "Welcome to our website!",
            "btn_get_started": "Get Started"
        },
        "navigation": {
            "menu_about": "About",
            "menu_contact": "Contact"
        }
    },
    "total_labels": 4
}
```

#### Get Detailed Label Information (Admin only)
```http
GET /api/language-labels?language_id=1
Authorization: Basic admin@karsaaz.com:Admin123
```

## 💡 Usage Examples

### Frontend Integration

#### React Example
```javascript
// Fetch labels for a specific language
const fetchLabels = async (languageCode) => {
    const response = await fetch(`/api/languages/${languageCode}/labels`);
    const data = await response.json();
    return data.labels;
};

// Usage in component
const labels = await fetchLabels('en');
console.log(labels.home.text_welcome); // "Welcome to our website!"
```

#### Vue.js Example
```javascript
// Store labels in Vuex/Pinia
const labelStore = {
    state: {
        currentLanguage: 'en',
        labels: {}
    },
    actions: {
        async loadLabels(languageId) {
            const response = await fetch(`/api/languages/${languageId}/labels`);
            const data = await response.json();
            this.labels = data.labels;
        }
    }
};
```

### Backend Integration

#### Python Client Example
```python
import requests

# Admin credentials
auth = ('admin@karsaaz.com', 'Admin123')

# Add a new translation
def add_translation(language_id, label_code_id, text):
    validation_data = {
        "language_id": language_id,
        "label_group_id": 1,  # Will be validated
        "label_code_id": label_code_id,
        "label_text": text
    }
    
    response = requests.post(
        'http://localhost:8004/api/labels/insert-with-validation',
        json=validation_data,
        auth=auth
    )
    
    return response.json()

# Usage
result = add_translation(
    language_id=4,  # German
    label_code_id=1,  # text_welcome
    text="Willkommen auf unserer Website!"
)
print(result['message'])
```

## 🔒 Authentication

Most endpoints require admin authentication:
- **Username**: `admin@karsaaz.com`
- **Password**: `Admin123`

Public endpoints (no authentication required):
- `GET /api/languages`
- `GET /api/languages/{language_id}`
- `GET /api/languages/{language_id}/labels`
- `GET /api/label-groups`
- `GET /api/label-codes/{code_id}`

## 🛠️ Development Workflow

### Adding a New Language

1. **Create the language**:
   ```bash
   curl -X POST "http://localhost:8004/api/languages" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"name": "German", "code": "de", "is_active": true}'
   ```

2. **Add translations for existing label codes**:
   ```bash
   curl -X POST "http://localhost:8004/api/language-labels" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"language_id": 4, "label_id": 1, "label_text": "Willkommen!"}'
   ```

### Adding a New Feature Section

1. **Create a label group**:
   ```bash
   curl -X POST "http://localhost:8004/api/label-groups" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"name": "pricing", "description": "Pricing page labels"}'
   ```

2. **Add label codes**:
   ```bash
   curl -X POST "http://localhost:8004/api/label-codes" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"code": "text_price", "description": "Price label", "label_group_id": 6}'
   ```

3. **Add translations for each language**:
   ```bash
   # English
   curl -X POST "http://localhost:8004/api/language-labels" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"language_id": 1, "label_id": 19, "label_text": "Price"}'
   
   # Spanish
   curl -X POST "http://localhost:8004/api/language-labels" \
        -H "Content-Type: application/json" \
        -u "admin@karsaaz.com:Admin123" \
        -d '{"language_id": 2, "label_id": 19, "label_text": "Precio"}'
   ```

## 🚨 Error Handling

### Common Error Responses

#### Validation Failed
```json
{
    "step": "validation",
    "success": false,
    "validation_result": {
        "valid": false,
        "language_exists": true,
        "label_group_exists": false,
        "label_code_exists": false,
        "message": "❌ Validation failed: Label group not found, Label code not found or doesn't belong to the specified group"
    },
    "message": "❌ Validation failed: Label group not found, Label code not found or doesn't belong to the specified group"
}
```

#### Duplicate Translation
```json
{
    "detail": "Language label already exists for this language and label code"
}
```

#### Authentication Required
```json
{
    "detail": "Invalid authentication credentials"
}
```

## 📊 Monitoring & Analytics

### Database Queries for Analytics

```sql
-- Count translations per language
SELECT l.name, l.code, COUNT(ll.id) as translation_count
FROM languages l
LEFT JOIN language_label ll ON l.id = ll.language_id
GROUP BY l.id, l.name, l.code
ORDER BY translation_count DESC;

-- Find missing translations
SELECT l.name as language, lg.name as group_name, lc.code as label_code
FROM languages l
CROSS JOIN label_codes lc
JOIN label_groups lg ON lc.label_group_id = lg.id
LEFT JOIN language_label ll ON l.id = ll.language_id AND lc.id = ll.label_id
WHERE ll.id IS NULL AND l.is_active = true
ORDER BY l.name, lg.name, lc.code;

-- Translation completion percentage
SELECT 
    l.name,
    COUNT(ll.id) as completed_translations,
    (SELECT COUNT(*) FROM label_codes) as total_labels,
    ROUND(COUNT(ll.id) * 100.0 / (SELECT COUNT(*) FROM label_codes), 2) as completion_percentage
FROM languages l
LEFT JOIN language_label ll ON l.id = ll.language_id
WHERE l.is_active = true
GROUP BY l.id, l.name
ORDER BY completion_percentage DESC;
```

## 🔄 Migration from Existing Systems

If you have existing translation files (JSON, YAML, etc.), you can create a migration script:

```python
import json
import asyncio
from app.services import LanguageService, LabelGroupService, LabelCodeService, LanguageLabelService

async def migrate_from_json(json_file_path):
    """Migrate from existing JSON translation files"""
    with open(json_file_path, 'r') as f:
        translations = json.load(f)
    
    # Process and insert translations
    # Implementation depends on your JSON structure
    pass
```

## 🎯 Best Practices

1. **Naming Conventions**:
   - Use descriptive label codes: `text_welcome`, `btn_submit`, `error_required`
   - Group related labels: `home`, `navigation`, `forms`
   - Use consistent prefixes: `text_`, `btn_`, `error_`, `label_`

2. **Translation Management**:
   - Always validate before inserting
   - Keep translations consistent in tone and style
   - Use placeholder syntax for dynamic content: `Hello {name}!`

3. **Performance**:
   - Cache frequently accessed translations
   - Use the bulk query endpoint: `/api/languages/{id}/labels`
   - Consider lazy loading for large translation sets

4. **Security**:
   - Protect admin endpoints with proper authentication
   - Validate and sanitize all translation text
   - Use HTTPS in production

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check database connection
   curl http://localhost:8004/health
   ```

2. **Authentication Problems**:
   ```bash
   # Test authentication
   curl -u "admin@karsaaz.com:Admin123" http://localhost:8004/api/language-labels
   ```

3. **Validation Failures**:
   - Ensure language, label group, and label code exist
   - Check that label code belongs to the specified group
   - Verify IDs are correct

### Debug Mode

Set environment variable for detailed logging:
```bash
export LOG_LEVEL=DEBUG
python3 start.py
```

## 📈 Future Enhancements

Potential improvements to consider:

1. **Import/Export**: Bulk import/export of translations
2. **Version Control**: Track changes to translations
3. **Approval Workflow**: Review process for translations
4. **Context Information**: Add context/screenshots for translators
5. **Pluralization**: Support for plural forms
6. **RTL Support**: Right-to-left language support
7. **Translation Memory**: Reuse similar translations
8. **Quality Assurance**: Translation validation rules

---

This multi-language label management system provides a robust foundation for internationalization in your application. The API endpoints directly correspond to the SQL validation and insertion process you provided, ensuring data integrity and proper workflow management. 