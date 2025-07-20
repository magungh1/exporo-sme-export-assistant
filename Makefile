# Exporo SME Export Assistant - Makefile
# Simplifies common development and deployment tasks

.PHONY: help run install clean test lint format check deps reset-db

# Default target
help:
	@echo "🚀 Exporo SME Export Assistant - Available Commands:"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install     - Install dependencies using uv"
	@echo "  make deps        - Show dependency tree"
	@echo ""
	@echo "🏃 Running the Application:"
	@echo "  make run         - Start the Streamlit application"
	@echo "  make dev         - Run in development mode with file watching"
	@echo ""
	@echo "🧹 Development Tools:"
	@echo "  make clean       - Clean up cache and temporary files"
	@echo "  make reset-db    - Reset the SQLite database"
	@echo "  make format      - Format code with black (if available)"
	@echo "  make lint        - Run linting checks (if available)"
	@echo "  make check       - Check imports and basic syntax"
	@echo ""
	@echo "🧪 Testing & Validation:"
	@echo "  make test        - Run basic functionality tests"
	@echo "  make validate    - Validate environment setup"
	@echo ""
	@echo "📊 Project Info:"
	@echo "  make info        - Show project information"
	@echo "  make size        - Show project size statistics"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing dependencies with uv..."
	uv sync
	@echo "✅ Dependencies installed successfully!"

# Run the application
run:
	@echo "🚀 Starting Exporo SME Export Assistant..."
	@echo "🗄️ Initializing database..."
	@mkdir -p data
	@echo "📱 Open your browser at: http://localhost:8501"
	@echo "🔑 Make sure your .env file is configured with GEMINI_API_KEY"
	@echo ""
	uv run streamlit run app.py

# Run in development mode with file watching
dev:
	@echo "🔧 Starting in development mode with file watching..."
	@echo "🗄️ Initializing database..."
	@mkdir -p data
	@echo "📱 Open your browser at: http://localhost:8501"
	@echo "🔄 App will reload automatically when files change"
	@echo ""
	uv run streamlit run app.py --server.fileWatcherType poll

# Clean up cache and temporary files
clean:
	@echo "🧹 Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .streamlit/ 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Reset database
reset-db:
	@echo "🗄️ Resetting SQLite database..."
	rm -f data/langkah_ekspor.db
	@echo "✅ Database reset! New database will be created on next run."

# Format code (if black is available)
format:
	@echo "🎨 Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black src/ --line-length 100; \
		echo "✅ Code formatted with black!"; \
	else \
		echo "⚠️ black not available. Install with: pip install black"; \
	fi

# Lint code (if available)
lint:
	@echo "🔍 Running linting checks..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ --max-line-length=100 --ignore=E203,W503; \
		echo "✅ Linting completed!"; \
	else \
		echo "⚠️ flake8 not available. Install with: pip install flake8"; \
	fi

# Check imports and basic syntax
check:
	@echo "🔍 Checking imports and syntax..."
	uv run python -c "from src.exporo import config, auth, chat; print('✅ All imports working!')"
	uv run python -c "from src.exporo.main import main; print('✅ Main function accessible!')"
	@echo "✅ Basic checks passed!"

# Show dependency tree
deps:
	@echo "📦 Dependency information:"
	@echo ""
	uv tree || echo "📋 Dependencies listed in pyproject.toml"

# Run basic functionality tests
test:
	@echo "🧪 Running basic functionality tests..."
	@echo "Testing environment variables..."
	uv run python -c "from src.exporo.config import GEMINI_API_KEY; print('✅ Environment variables loaded!' if GEMINI_API_KEY else '❌ GEMINI_API_KEY not configured')"
	@echo "Testing database initialization..."
	uv run python -c "from src.exporo.auth import init_db; init_db(); print('✅ Database initialization works!')"
	@echo "Testing AI integration..."
	uv run python -c "from src.exporo.chat import init_gemini; init_gemini(); print('✅ Gemini AI connection works!')" 2>/dev/null || echo "❌ Gemini AI connection failed - check your API key"
	@echo "✅ Basic tests completed!"

# Validate environment setup
validate:
	@echo "🔍 Validating environment setup..."
	@echo ""
	@echo "📋 Checking Python version..."
	@python3 --version || echo "❌ Python not found"
	@echo ""
	@echo "📋 Checking uv installation..."
	@uv --version || echo "❌ uv not found"
	@echo ""
	@echo "📋 Checking project structure..."
	@test -f pyproject.toml && echo "✅ pyproject.toml found" || echo "❌ pyproject.toml missing"
	@test -f .env && echo "✅ .env file found" || echo "⚠️ .env file missing - copy from .env.example"
	@test -f .env.example && echo "✅ .env.example found" || echo "❌ .env.example missing"
	@test -d src/exporo && echo "✅ Source directory found" || echo "❌ src/exporo directory missing"
	@echo ""
	@echo "📋 Checking core files..."
	@test -f src/exporo/main.py && echo "✅ main.py found" || echo "❌ main.py missing"
	@test -f src/exporo/config.py && echo "✅ config.py found" || echo "❌ config.py missing"
	@test -f src/exporo/auth.py && echo "✅ auth.py found" || echo "❌ auth.py missing"
	@test -f src/exporo/chat.py && echo "✅ chat.py found" || echo "❌ chat.py missing"
	@echo ""

# Show project information
info:
	@echo "📊 Exporo SME Export Assistant - Project Information"
	@echo ""
	@echo "🏗️ Architecture: Modular Python package with Streamlit frontend"
	@echo "🤖 AI Engine: Google Gemini 2.5 Flash for chat & Gemini 2.0 Flash for export analysis"
	@echo "💾 Database: SQLite for user management"
	@echo "📦 Package Manager: uv (ultrafast Python package installer)"
	@echo "🌐 Framework: Streamlit web application"
	@echo ""
	@echo "📁 Key Directories:"
	@echo "  src/exporo/     - Main application code"
	@echo "  docs/           - Documentation and diagrams"
	@echo "  data/           - Database files"
	@echo ""
	@echo "🔗 Repository: https://github.com/magungh1/exporo-sme-export-assistant"

# Show project size statistics
size:
	@echo "📏 Project Size Statistics:"
	@echo ""
	@echo "📂 Directory sizes:"
	@du -sh src/ docs/ 2>/dev/null || echo "Unable to calculate directory sizes"
	@echo ""
	@echo "📄 File counts:"
	@echo "Python files: $$(find src/ -name '*.py' | wc -l | tr -d ' ')"
	@echo "Documentation files: $$(find docs/ -name '*.md' | wc -l | tr -d ' ')"
	@echo "Total files: $$(find . -type f ! -path './.git/*' ! -path './.*' | wc -l | tr -d ' ')"
	@echo ""
	@echo "📝 Lines of code:"
	@echo "Python LOC: $$(find src/ -name '*.py' -exec cat {} \; | wc -l | tr -d ' ')"

# Quick start for new users
quickstart: install validate
	@echo ""
	@echo "🎉 Exporo is ready to go!"
	@echo ""
	@echo "🔑 Next steps:"
	@echo "1. Make sure your .env file has GEMINI_API_KEY configured"
	@echo "2. Run 'make run' to start the application"
	@echo "3. Open http://localhost:8501 in your browser"
	@echo ""
	@echo "💡 Tip: Use 'make help' to see all available commands"