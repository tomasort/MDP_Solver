# MDP Solver Web UI

A modern web interface for the Markov Decision Process (MDP) Solver.

## Project Structure

```
web_ui/
├── app.py                  # Main Flask application (refactored with blueprints)
├── run.py                  # Application startup script
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── blueprints/            # Flask blueprints for modular organization
│   ├── __init__.py
│   ├── main.py            # Main routes (homepage)
│   ├── api.py             # API endpoints
│   └── errors.py          # Error handling
├── services/              # Business logic services
│   ├── __init__.py
│   ├── mdp_service.py     # MDP solving operations
│   └── example_service.py # Example management
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css      # Custom styling
│   └── js/
│       ├── main.js        # Main JavaScript functionality
│       └── graph.js       # Graph visualization
├── templates/             # Jinja2 templates
│   ├── base.html          # Base template
│   └── index.html         # Main interface
└── app_old.py            # Backup of original monolithic app
```

## Architecture

### Blueprints
- **main**: Handles the main web interface routes
- **api**: RESTful API endpoints for MDP operations
- **errors**: Centralized error handling

### Services
- **MDPSolverService**: Handles MDP validation and solving
- **ExampleService**: Manages loading and serving example MDPs

### Configuration
- **Development**: Debug mode enabled, running on port 5003
- **Production**: Debug disabled, configurable port

## Running the Application

### Method 1: Using the startup script (Recommended)
```bash
source venv/bin/activate
cd web_ui
python run.py
```

### Method 2: Using Flask directly
```bash
source venv/bin/activate
cd web_ui
python app.py
```

### Method 3: Using environment variables
```bash
source venv/bin/activate
cd web_ui
export FLASK_ENV=production
python run.py
```

## API Endpoints

### GET /
Main web interface

### POST /api/validate
Validate MDP input text
- **Body**: `{"input": "MDP definition text"}`
- **Response**: Validation results with node statistics

### POST /api/solve
Solve MDP problem
- **Body**: `{"input": "MDP text", "discountFactor": 1.0, "tolerance": 0.01, "maxIterations": 100, "minimize": false}`
- **Response**: Solution with policy, values, and graph data

### GET /api/examples
Get all available example MDPs
- **Response**: Array of example objects with content

### GET /api/examples/<filename>
Get specific example by filename
- **Response**: Single example object

## Features

- ✅ **Modular Architecture**: Clean separation with Flask blueprints
- ✅ **Service Layer**: Business logic separated from routing
- ✅ **Configuration Management**: Environment-based configuration
- ✅ **Error Handling**: Centralized error handling for web and API
- ✅ **Real-time Validation**: Input validation with live feedback
- ✅ **Interactive Visualization**: D3.js-powered graph rendering
- ✅ **Example Library**: Pre-loaded example MDPs
- ✅ **Responsive Design**: Mobile-friendly interface

## Development

### Adding New Features
1. **New API endpoints**: Add to `blueprints/api.py`
2. **New pages**: Add routes to `blueprints/main.py` and templates
3. **Business logic**: Add services to `services/` directory
4. **Configuration**: Update `config.py`

### Code Organization Principles
- **Blueprints**: Group related routes together
- **Services**: Keep business logic separate from web logic
- **Configuration**: Environment-based settings
- **Templates**: Reusable Jinja2 templates
- **Static files**: Organized by type (CSS, JS)

## Benefits of Refactoring

1. **Maintainability**: Code is now organized into logical modules
2. **Scalability**: Easy to add new features without affecting existing code
3. **Testing**: Services can be unit tested independently
4. **Deployment**: Configuration-based deployment options
5. **Collaboration**: Multiple developers can work on different blueprints
6. **Reusability**: Services can be reused across different interfaces
