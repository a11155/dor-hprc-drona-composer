---
sidebar_position: 4
---

# Installation & Development Setup

This guide covers setting up Drona Composer for development and deployment.

## Development Environment

### Prerequisites

Ensure you have the following installed:

- **Node.js** (v18 or higher)
- **npm** (v8 or higher)
- **Python** (v3.8 or higher)
- **Git**

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/tamu-edu/dor-hprc-drona-composer.git
cd dor-hprc-drona-composer

# Install frontend dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Start development servers
npm run build-watch  # Frontend development server
python app.py        # Backend development server
```

## Detailed Installation

### Frontend Setup

#### Install Dependencies
```bash
npm install
```

#### Development Scripts
```bash
# Build for development
npm run build

# Build for production
npm run build:prod

# Watch for changes (development)
npm run build-watch

# Run tests
npm run test

# Generate documentation
npm run docs
```

### Backend Setup

#### Python Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Flask Application
```bash
# Development mode
export FLASK_ENV=development
python app.py

# Production mode
export FLASK_ENV=production
python app.py
```

### Configuration

#### Environment Variables

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key-here

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=5000

# HPC Integration
SLURM_ENABLED=False
CLUSTER_CONFIG_PATH=/path/to/cluster/config

# File Storage
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=100MB

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

#### Application Configuration

Edit `config.yml`:

```yaml
# Application Configuration
app:
  name: "Drona Composer"
  version: "1.0.0"
  debug: true

# Database Configuration (if applicable)
database:
  url: "sqlite:///drona.db"
  echo: false

# HPC Configuration
hpc:
  enabled: false
  clusters:
    - name: "grace"
      host: "grace.hprc.tamu.edu"
      scheduler: "slurm"
    - name: "terra"
      host: "terra.hprc.tamu.edu"
      scheduler: "slurm"

# Security Settings
security:
  csrf_enabled: true
  session_timeout: 3600
  max_file_size: "100MB"
```

## Project Structure

Understanding the codebase organization:

```
dor-hprc-drona-composer/
├── src/                          # React frontend source
│   ├── components/               # React components
│   ├── hooks/                    # Custom React hooks
│   ├── context/                  # React context providers
│   └── index.js                  # Main entry point
├── views/                        # Python backend routes
│   ├── job_composer.py          # Job management endpoints
│   ├── file_utils.py            # File operation handlers
│   ├── schema_routes.py         # Schema processing routes
│   └── socket_handler.py        # WebSocket handlers
├── machine_driver_scripts/      # HPC integration utilities
│   ├── engine.py                # Job execution engine
│   └── utils.py                 # Helper utilities
├── environments/                # Environment configurations
│   ├── demo-drona-env/          # Demo environment
│   └── [custom-environments]/   # Custom environments
├── static/                      # Static assets
├── templates/                   # HTML templates
├── docs/                        # Documentation (current)
└── website/                     # Docusaurus documentation
```

## Docker Setup

For containerized deployment:

### Dockerfile

```dockerfile
FROM node:18-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src/ ./src/
COPY webpack.config.js babel.config.js ./
RUN npm run build:prod

FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY --from=frontend /app/static/dist ./static/dist

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  drona-composer:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./environments:/app/environments
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - drona-composer
    restart: unless-stopped
```

## Production Deployment

### Requirements

- **Linux server** (Ubuntu 20.04+ recommended)
- **Reverse proxy** (Nginx, Apache)
- **SSL certificate** for HTTPS
- **Process manager** (systemd, supervisor)

### System Service

Create `/etc/systemd/system/drona-composer.service`:

```ini
[Unit]
Description=Drona Composer Application
After=network.target

[Service]
Type=simple
User=drona
WorkingDirectory=/opt/drona-composer
Environment=FLASK_ENV=production
ExecStart=/opt/drona-composer/.venv/bin/python app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable drona-composer
sudo systemctl start drona-composer
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /static/ {
        alias /opt/drona-composer/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Development Workflow

### Making Changes

1. **Frontend Development**
   ```bash
   npm run build-watch
   ```

2. **Backend Development**
   ```bash
   # Run with auto-reload
   export FLASK_ENV=development
   python app.py
   ```

3. **Testing**
   ```bash
   # Frontend tests
   npm test

   # Backend tests (if implemented)
   python -m pytest
   ```

### Building for Production

```bash
# Build optimized frontend
npm run build:prod

# Verify Python dependencies
pip freeze > requirements.txt

# Test production configuration
export FLASK_ENV=production
python app.py
```

## Troubleshooting

### Common Issues

#### Frontend Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Python Module Errors
```bash
# Verify virtual environment
which python
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x setup.sh
chown -R user:user /path/to/project
```

### Performance Optimization

1. **Frontend Optimization**
   - Enable gzip compression
   - Use CDN for static assets
   - Implement code splitting

2. **Backend Optimization**
   - Use production WSGI server (gunicorn)
   - Enable caching
   - Optimize database queries

3. **System Optimization**
   - Monitor resource usage
   - Configure log rotation
   - Set up monitoring and alerts

## Next Steps

After successful installation:

1. **Configure Environments** - Set up your HPC environments
2. **Customize Schemas** - Create forms for your specific workflows
3. **Set Up Monitoring** - Implement logging and monitoring
4. **Security Hardening** - Configure authentication and SSL
5. **Backup Strategy** - Set up regular backups for configurations

For detailed configuration guides, see the [Environment Management](../environments/creating-environments) section.