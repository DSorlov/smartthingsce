# Contributing to SmartThings Community Edition

Thank you for your interest in contributing to the SmartThings Community Edition integration for Home Assistant!

## Development Setup

### Prerequisites
- Python 3.11 or newer
- Home Assistant development environment
- Docker and Docker Compose
- Git

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DSorlov/smartthingsce.git
   cd smartthingsce
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Run tests and validation:**
   ```bash
   # Validate Python syntax
   python -m py_compile custom_components/smartthingsce/*.py
   
   # Run linting
   black --check custom_components/
   isort --check-only custom_components/
   flake8 custom_components/
   
   # Type checking
   mypy custom_components/smartthingsce/
   ```

### Using Docker Development Environment

The project includes a Docker-based development environment:

```bash
# Start development environment
docker-compose up -d

# Run validation
docker-compose exec dev ./scripts/validate.sh

# Run tests
docker-compose exec dev pytest

# Format code
docker-compose exec dev black custom_components/
docker-compose exec dev isort custom_components/

# Stop environment
docker-compose down
```

## Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks for code quality

### Running Code Quality Checks

```bash
# Format code
black custom_components/
isort custom_components/

# Check formatting
black --check custom_components/
isort --check-only custom_components/

# Lint code
flake8 custom_components/

# Type checking
mypy custom_components/smartthingsce/
```

## Testing

### Automated Testing

The project includes GitHub Actions workflows that run:

1. **hassfest**: Validates Home Assistant integration requirements
2. **HACS**: Validates HACS compatibility
3. **CI**: Runs linting, formatting checks, and Python validation
4. **Translation validation**: Ensures all translation files are consistent

### Manual Testing

1. **Install in Home Assistant:**
   - Copy `custom_components/smartthingsce` to your HA `custom_components` folder
   - Restart Home Assistant
   - Add the integration through the UI

2. **Test different scenarios:**
   - Valid SmartThings tokens
   - Invalid tokens
   - Network connectivity issues
   - Different device types
   - Webhook subscriptions
   - Real-time event handling

## Adding New Device Support

To add support for a new SmartThings capability:

1. **Add capability mapping** in `custom_components/smartthingsce/capabilities.py`
2. **Create entity class** if needed in appropriate file (e.g., `sensor.py`, `switch.py`)
3. **Add translations** for the new capability in translation files
4. **Test thoroughly** with actual devices
5. **Document** the new capability in README.md

## Adding Translations

To add a new language translation:

1. **Create translation file:**
   ```bash
   cp custom_components/smartthingsce/translations/en.json custom_components/smartthingsce/translations/[language_code].json
   ```

2. **Translate all strings** in the new file

3. **Validate translation:**
   ```bash
   python -c "import json; json.load(open('custom_components/smartthingsce/translations/[language_code].json', encoding='utf-8'))"
   ```

4. **Test the translation** by changing your Home Assistant language

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code quality guidelines
3. **Add tests** for new functionality (if applicable)
4. **Update documentation** if needed
5. **Run all quality checks** before submitting
6. **Create a pull request** with a clear description

### Pull Request Checklist

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] Documentation has been updated
- [ ] Translation files are consistent (if modified)
- [ ] Commit messages are clear and descriptive
- [ ] Pre-commit hooks pass
- [ ] CHANGELOG.md has been updated

## Release Process

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## SmartThings API Guidelines

When working with the SmartThings API:

1. **Use async operations** for all API calls
2. **Handle rate limiting** appropriately
3. **Implement proper error handling** for API failures
4. **Cache data** when appropriate to reduce API calls
5. **Follow SmartThings best practices** from their documentation

## Code Style Guidelines

### Python Code Style

- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use descriptive variable names
- Follow PEP 8 style guide

### Example:

```python
async def get_device_status(
    device_id: str, 
    capability: str
) -> Dict[str, Any]:
    """Get the current status of a device capability.
    
    Args:
        device_id: The SmartThings device ID
        capability: The capability to query
        
    Returns:
        Dictionary containing the capability status
        
    Raises:
        SmartThingsAPIError: If the API request fails
    """
    try:
        response = await self._api_call(f"devices/{device_id}/status")
        return response.get(capability, {})
    except Exception as err:
        raise SmartThingsAPIError(f"Failed to get device status: {err}")
```

## Getting Help

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Code Review**: Submit PRs for community review

## Code of Conduct

Please be respectful and constructive in all interactions. This project welcomes contributions from everyone regardless of background or experience level.

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- GitHub contributors page

Thank you for contributing to SmartThings Community Edition! 🎉
