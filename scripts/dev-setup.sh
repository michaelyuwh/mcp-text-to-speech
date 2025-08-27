#!/bin/bash
# Development script for MCP Text-to-Speech Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main function
main() {
    print_status "Setting up MCP Text-to-Speech development environment..."
    
    # Check Python version
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    print_status "Python version: $python_version"
    
    if [[ $(echo "$python_version 3.9" | awk '{print ($1 >= $2)}') == 0 ]]; then
        print_error "Python 3.9+ is required, found $python_version"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip and install uv
    print_status "Installing/upgrading package managers..."
    pip install --upgrade pip uv
    
    # Install development dependencies
    print_status "Installing dependencies..."
    uv pip install -e ".[dev]"
    
    # Install system TTS engines (if on Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Checking system TTS engines..."
        
        if command_exists apt-get; then
            print_status "Installing system TTS engines with apt..."
            sudo apt-get update
            sudo apt-get install -y espeak espeak-data festival festvox-kallpc16k sox alsa-utils
            print_success "System TTS engines installed"
        elif command_exists yum; then
            print_status "Installing system TTS engines with yum..."
            sudo yum install -y espeak espeak-devel festival sox alsa-utils
            print_success "System TTS engines installed"
        else
            print_warning "Could not detect package manager. Please install espeak and festival manually."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            print_status "Installing system TTS engines with Homebrew..."
            brew install espeak festival sox
            print_success "System TTS engines installed"
        else
            print_warning "Homebrew not found. Please install espeak and festival manually."
        fi
    fi
    
    # Create necessary directories
    print_status "Creating directories..."
    mkdir -p output tests logs
    
    # Run environment check
    print_status "Checking TTS environment..."
    python -m mcp_text_to_speech --info
    
    print_success "Development environment setup complete!"
    print_status "To activate the environment, run: source venv/bin/activate"
    print_status "To run the server, use: python -m mcp_text_to_speech"
    print_status "To run tests, use: pytest tests/"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    source venv/bin/activate
    
    # Unit tests
    if [ -d "tests" ]; then
        pytest tests/ -v
    else
        print_warning "No tests directory found"
    fi
    
    # Integration tests
    print_status "Running integration tests..."
    python -m mcp_text_to_speech --info
}

# Function to run linting and formatting
run_lint() {
    print_status "Running code quality checks..."
    source venv/bin/activate
    
    # Black formatting
    print_status "Running Black formatter..."
    black src/ --check
    
    # isort import sorting
    print_status "Running isort..."
    isort src/ --check-only
    
    # flake8 linting
    print_status "Running flake8..."
    flake8 src/
    
    # mypy type checking
    print_status "Running mypy type checking..."
    mypy src/
    
    print_success "Code quality checks passed!"
}

# Function to fix code formatting
fix_code() {
    print_status "Fixing code formatting..."
    source venv/bin/activate
    
    black src/
    isort src/
    
    print_success "Code formatting fixed!"
}

# Function to clean environment
clean() {
    print_status "Cleaning development environment..."
    
    # Remove virtual environment
    if [ -d "venv" ]; then
        rm -rf venv
        print_success "Virtual environment removed"
    fi
    
    # Remove cache directories
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Cache files cleaned"
}

# Parse command line arguments
case "${1:-setup}" in
    setup)
        main
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    fix)
        fix_code
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        echo "MCP Text-to-Speech Development Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup     Set up development environment (default)"
        echo "  test      Run tests"
        echo "  lint      Run code quality checks"
        echo "  fix       Fix code formatting"
        echo "  clean     Clean environment and cache files"
        echo "  help      Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
