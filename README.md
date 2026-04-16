# Green Campus Alert System 🌿

An AI-powered system for monitoring and managing campus vegetation health through intelligent image analysis.

## Features

- 🤖 **AI Image Analysis**: Automatic classification of vegetation health using machine learning
- 📱 **Web Interface**: Clean, responsive web application for easy access
- 📊 **Alert Management**: Real-time alerts for vegetation issues
- 🌱 **Campus Monitoring**: Comprehensive campus vegetation health tracking
- 📈 **Data Analytics**: Historical data and trend analysis (coming soon)

## Project Structure

```
green-campus-alert/
├── backend/              # Flask REST API
│   ├── app.py           # Main application
│   ├── config.py        # Configuration
│   ├── database.py      # Database models
│   ├── ml_module.py     # ML analysis engine
│   ├── requirements.txt # Python dependencies
│   ├── uploads/         # User uploads
│   └── ml_models/       # Trained ML models
├── frontend/            # Web interface
│   ├── index.html       # Main page
│   ├── css/style.css    # Styles
│   └── js/app.js        # Client-side logic
├── scripts/             # Setup and start scripts
│   ├── setup.sh/bat     # Installation scripts
│   └── start.sh/bat     # Launch scripts
├── docs/                # Documentation
│   ├── database_schema.sql
│   └── api_docs.md
├── ml_data/             # Training data
└── logs/                # Application logs
```

## Prerequisites

- Python 3.8+
- Node.js (optional, for frontend tools)
- SQLite or PostgreSQL
- pip package manager

## Installation

### Windows
```bash
cd scripts
setup.bat
```

### Linux/macOS
```bash
cd scripts
chmod +x setup.sh
./setup.sh
```

## Running the Application

### Windows
```bash
cd scripts
start.bat
```

### Linux/macOS
```bash
cd scripts
chmod +x start.sh
./start.sh
```

The application will be available at:
- **Frontend**: http://localhost:5000
- **API**: http://localhost:5000/api

## API Documentation

See [API Documentation](docs/api_docs.md) for complete API reference.

### Quick Start Example

```bash
# Health check
curl http://localhost:5000/api/health

# Analyze an image
curl -X POST -F "image=@path/to/image.jpg" http://localhost:5000/api/analyze
```

## Configuration

Edit `backend/config.py` to modify:
- Database connection string
- Upload folder path
- ML model location
- Flask settings

## Database

The application uses SQLAlchemy ORM with SQLite by default.

### Schema
- **users**: User accounts and roles
- **alerts**: Campus alerts and notifications
- **logs**: Application activity logs

See [Database Schema](docs/database_schema.sql) for details.

## Machine Learning Module

The `ml_module.py` handles image analysis using trained models.

**Supported Classifications:**
- Healthy: Vegetation is in good condition
- Diseased: Plant disease detected
- Damaged: Physical damage to vegetation
- Alert: Requires immediate attention

## Development

### Backend Development
```bash
# Install dev dependencies
pip install flask-testing pytest

# Run tests
pytest
```

### Frontend Development
Modify `frontend/js/app.js` and `frontend/css/style.css`

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on the project repository.

## Future Enhancements

- User authentication system
- Advanced analytics dashboard
- Mobile app integration
- Real-time notification system
- Integration with campus management systems
- Predictive maintenance recommendations
- Multi-language support

## Authors

Green Campus Initiative Team

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Basic image analysis
- Web interface
- API endpoints
