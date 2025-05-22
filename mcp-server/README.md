# CVE Database MCP Server

Model Context Persistence (MCP) server for CVE database interactions. This server provides endpoints for:

- Querying CVE data
- Retrieving database schema
- Getting sample data from tables
- Health checks

## Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your database credentials:
   - For local development, use your local PostgreSQL credentials
   - For GCP deployment, use Cloud SQL credentials

3. Never commit `.env` files to version control

## Database Setup

1. Initialize the database:
```bash
python db/init_db.py
```

2. Import data:
   - Use Cloud SQL import feature to import your CVE data
   - Or use psql to import from SQL dump:
   ```bash
   psql -h [HOST] -U [USER] -d [DATABASE] -f your_data.sql
   ```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Docker

Build and run with Docker:
```bash
docker build -t mcp-server .
docker run -p 8081:8080 \
  --env-file .env \
  mcp-server
```

## GCP Deployment

### Setting up Cloud SQL

1. Create a Cloud SQL instance:
```bash
gcloud sql instances create cve-database \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

2. Store credentials in Secret Manager:
```bash
gcloud secrets create db-credentials --replication-policy="automatic"
gcloud secrets versions add db-credentials --data-file=".env"
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy mcp-server \
    --image gcr.io/$PROJECT_ID/mcp-server \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets=DB_USER=db-credentials:DB_USER:latest,DB_PASSWORD=db-credentials:DB_PASSWORD:latest
```

### Security Best Practices

1. Use Secret Manager for all credentials
2. Enable Cloud SQL Auth Proxy in production
3. Set up proper IAM roles and permissions
4. Enable audit logging
5. Regularly rotate credentials
6. Use SSL/TLS for database connections

## API Endpoints

- GET `/schema` - Get database schema
- POST `/query` - Execute SQL queries
- GET `/tables/{table_name}/sample` - Get sample data from tables
- GET `/health` - Health check

## Security Considerations

1. Database Access:
   - Use least privilege principle
   - Create read-only users where possible
   - Use connection pooling in production

2. API Security:
   - Consider adding authentication for production
   - Implement rate limiting
   - Add query validation and sanitization

3. Cloud Security:
   - Use VPC-native Cloud Run
   - Enable Cloud Audit Logs
   - Regular security scanning
