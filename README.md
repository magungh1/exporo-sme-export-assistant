# 🚀 Exporo - SME Export Assistant

A friendly Business Profile Assistant helping Indonesian SMEs prepare for export through natural conversation and AI-powered data extraction.

DEMO: https://drive.google.com/file/d/1uSIRJQbKrhUMdipkv3BKiV4AlwJ5XbS3/view?usp=sharing
## ✨ Features

- **Authentication System** - Secure user registration and login
- **AI Chat Interface** - Natural conversation with Exporo bot in Bahasa Indonesia
- **Memory Bot** - Persistent data extraction and business profile building
- **Dark Sidebar Navigation** - Modern collapsible navigation with glassmorphism effects
- **Export Support** - Download business profiles as JSON
- **Modern UI** - WhatsApp-like chat interface with timestamps

## 🏗️ Architecture

```
src/exporo/
├── main.py      # Clean entry point & routing
├── config.py    # Shared configuration & constants
├── auth.py      # Authentication & user management
└── chat.py      # Chat interface & AI integration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- UV package manager
- Make (optional, for simplified commands)

### Installation

1. **Clone and navigate to project:**
   ```bash
   git clone https://github.com/magungh1/exporo-sme-export-assistant.git
   cd exporo-sme-export-assistant
   ```

2. **Quick setup with Makefile:**
   ```bash
   make install           # Install dependencies
   cp .env.example .env   # Copy environment template
   # Edit .env and add your GEMINI_API_KEY
   make run              # Start the application
   ```

3. **Or manual setup:**
   ```bash
   uv sync                                    # Install dependencies
   cp .env.example .env                       # Copy environment template
   # Edit .env and add your GEMINI_API_KEY
   uv run streamlit run app.py               # Run the application
   ```

### 🛠️ Available Make Commands

```bash
make help        # Show all available commands
make run         # Start the application
make dev         # Run in development mode with file watching
make install     # Install dependencies
make validate    # Check environment setup
make test        # Run basic functionality tests
make format      # Format code with ruff
make lint        # Lint code with ruff
make fix         # Format and lint code with ruff
make clean       # Clean up cache files
make reset-db    # Reset the database
```

### Environment Variables

Create a `.env` file with:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

## 🔄 Usage Flow

1. **Register/Login** - Create account or sign in
2. **Navigate** - Use the dark sidebar to access different features
3. **Chat with Exporo** - Answer questions about your business
4. **Memory Bot** - Watch as your business profile builds automatically
5. **Export Data** - Download your complete business profile

## 🛠️ Development

### Module Overview

- **`main.py`** - Application entry point and routing logic
- **`config.py`** - API keys, prompts, styles, and constants
- **`auth.py`** - User authentication and database operations
- **`chat.py`** - Chat interface and Gemini AI integration

### Running with UV
```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py

# Test imports
uv run python -c "from src.exporo import config, auth, chat; print('✅ All good!')"
```

### Running with Make
```bash
# Install and validate setup
make install validate

# Run the application
make run

# Development mode with file watching
make dev

# Run tests, format, and cleanup
make test fix clean
```

## 📁 File Structure

```
export/
├── src/exporo/          # Main application code
│   ├── main.py         # Entry point & routing
│   ├── config.py       # Configuration & styles
│   ├── auth.py         # Authentication system
│   └── chat.py         # Chat & AI integration
├── data/               # Database files
│   └── langkah_ekspor.db
├── docs/               # Documentation
├── screenshots/        # UI screenshots
├── archive/            # Legacy/backup files
├── app.py             # Application launcher
├── .env.example       # Environment template
├── pyproject.toml     # Dependencies
└── README.md          # This file
```

## 🔒 Security

- API keys stored in environment variables
- Password hashing with SHA-256
- SQLite database for user management
- Environment files gitignored

## 🤖 AI Integration

Uses Google's Gemini 2.5 Flash model for:
- Natural conversation in Bahasa Indonesia
- Business data extraction from conversations
- Structured JSON profile generation

## 📊 Data Structure

The Memory Bot extracts and stores:
- Company name and background
- Product details and categories
- Production capacity and location
- Export readiness information

## 🎨 UI Features

- **Dark Sidebar Navigation** - Collapsible sidebar with user profile and menu
- **WhatsApp-like Chat** - Familiar messaging interface
- **Blue/Cream Messages** - User (blue) and bot (cream) bubbles
- **Timestamps** - Real-time message timestamps
- **Image Support** - Product image uploads
- **Glassmorphism Effects** - Modern translucent design elements
- **Responsive Design** - Works on desktop and mobile

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

Built with ❤️ for Indonesian SMEs ready to go global! 🌍
