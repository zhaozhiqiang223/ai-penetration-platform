# Contributing to AI-Penetration-Platform

We welcome contributions to the AI-Penetration-Platform! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [License](#license)

## Code of Conduct

This project follows a strict code of conduct. Please be respectful and inclusive in all interactions.

### Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to a positive environment for our community:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior:

* The use of sexualized language or imagery and unwelcome sexual attention or advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- Docker (optional)

### Setup

1. Fork the repository
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/ai-penetration-platform.git
   cd ai-penetration-platform
   ```

3. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Set up the frontend:
   ```bash
   cd ../frontend
   npm install
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Run the development servers:
   ```bash
   # Backend
   cd backend
   python -m uvicorn api.main:app --reload

   # Frontend
   cd ../frontend
   npm start
   ```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bugfix-name
# or
git checkout -b docs/your-docs-changes
```

### 2. Make Changes

- Follow the code style guidelines
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

Write clear and descriptive commit messages:

```bash
git add .
git commit -m "feat: add new AI vulnerability detection feature"
# or
git commit -m "fix: resolve SQL injection detection bug"
# or
git commit -m "docs: update API documentation"
```

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title
- Detailed description
- Any relevant issues
- Screenshots if applicable

## Code Style

### Python

- Follow PEP 8
- Use black for code formatting
- Use flake8 for linting
- Use mypy for type checking

```bash
# Format code
black .

# Lint code
flake8 .

# Type check
mypy .
```

### JavaScript/TypeScript

- Use ESLint and Prettier
- Follow Airbnb JavaScript Style Guide

```bash
# Lint and format
npm run lint
npm run format
```

### General Guidelines

- Use meaningful variable and function names
- Write clear and concise comments
- Follow the existing code patterns
- Keep functions small and focused
- Write unit tests for new features

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
cd ..
python -m pytest tests/
```

### Test Coverage

- Aim for 80%+ test coverage
- Write tests for new features
- Update tests when modifying existing code
- Use mocking for external dependencies

### Test Structure

```
tests/
├── test_models.py      # Model tests
├── test_services.py   # Service tests
├── test_api.py        # API tests
└── integration/       # Integration tests
```

## Documentation

### Documentation Standards

- Keep documentation up to date with code changes
- Use clear and concise language
- Provide examples where helpful
- Include API documentation for new endpoints

### Documentation Types

- **README.md**: Project overview and setup
- **API Documentation**: Auto-generated from FastAPI docs
- **Code Documentation**: Docstrings and comments
- **User Guides**: Tutorials and usage examples

### Contributing to Documentation

- Update README.md for new features
- Add docstrings for new functions and classes
- Create or update user guides
- Fix typos and clarify existing documentation

## Submitting Changes

### Pull Request Guidelines

1. **Title**: Clear and descriptive
2. **Description**: Explain what changes were made and why
3. **Issues**: Reference any related issues
4. **Testing**: Describe how changes were tested
5. **Breaking Changes**: Clearly indicate any breaking changes

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Changes Made
- [x] Feature addition
- [x] Bug fix
- [x] Documentation update
- [x] Code refactoring

## Testing
- [x] Unit tests updated
- [x] Integration tests passed
- [x] Manual testing completed

## Related Issues
- Closes #123
- Related to #456

## Screenshots (if applicable)
![Screenshot](url)

## Breaking Changes
None
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment**: OS, Python version, Node.js version
2. **Steps to Reproduce**: Clear steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Error Messages**: Any error messages or stack traces
6. **Relevant Code**: Code snippets that demonstrate the issue

### Issue Template

```markdown
## Bug Report
**Title**: Brief description of the bug

**Environment**:
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.0]
- Node.js: [e.g., 18.0.0]
- Browser: [e.g., Chrome 91.0]

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**:
What should happen

**Actual Behavior**:
What actually happens

**Error Messages**:
```
Error message here
```

**Additional Context**:
Any other relevant information
```

## License

By contributing to AI-Penetration-Platform, you agree that your contributions will be licensed under the MIT License. Please see the [LICENSE](LICENSE) file for more information.

## Recognition

Contributors will be recognized in the project's contributors list and commit history. Significant contributors may be invited to join the core development team.

## Questions?

If you have any questions about contributing, please:

1. Check the existing issues and pull requests
2. Search the documentation
3. Ask in the project's discussions
4. Contact the maintainers

Thank you for contributing to AI-Penetration-Platform! 🚀