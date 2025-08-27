#!/bin/bash
# Docker deployment script for MCP Text-to-Speech Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="mcp-text-to-speech"
IMAGE_TAG="latest"
CONTAINER_NAME="mcp-tts-server"

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

# Function to check Docker
check_docker() {
    if ! command_exists docker; then
        print_error "Docker is required but not installed"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running"
        echo "Please start Docker daemon"
        exit 1
    fi
    
    print_success "Docker is available and running"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
    
    # Build single-platform image
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" .
    
    print_success "Docker image built successfully"
    
    # Show image info
    print_status "Image information:"
    docker images "$IMAGE_NAME:$IMAGE_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# Function to build multi-platform image
build_multiplatform() {
    print_status "Building multi-platform Docker image..."
    
    # Check if buildx is available
    if ! docker buildx version >/dev/null 2>&1; then
        print_error "Docker buildx is required for multi-platform builds"
        exit 1
    fi
    
    # Create builder if it doesn't exist
    docker buildx create --use --name multiplatform-builder 2>/dev/null || true
    
    # Build for multiple platforms
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t "$IMAGE_NAME:$IMAGE_TAG" \
        --push \
        .
    
    print_success "Multi-platform image built and pushed"
}

# Function to run container
run_container() {
    print_status "Starting container: $CONTAINER_NAME"
    
    # Stop existing container if running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_warning "Stopping existing container..."
        docker stop "$CONTAINER_NAME"
    fi
    
    # Remove existing container if exists
    if docker ps -a -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_warning "Removing existing container..."
        docker rm "$CONTAINER_NAME"
    fi
    
    # Create output directory
    mkdir -p ./output
    
    # Run container
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p 8000:8000 \
        -v "$(pwd)/output:/app/output" \
        -v tts_cache:/tmp/tts_cache \
        --device /dev/snd:/dev/snd 2>/dev/null || docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p 8000:8000 \
        -v "$(pwd)/output:/app/output" \
        -v tts_cache:/tmp/tts_cache \
        "$IMAGE_NAME:$IMAGE_TAG"
    
    print_success "Container started successfully"
    
    # Show container status
    docker ps -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Function to use Docker Compose
compose_up() {
    print_status "Starting services with Docker Compose..."
    
    if ! command_exists docker-compose; then
        print_error "docker-compose is required but not installed"
        exit 1
    fi
    
    # Build and start services
    docker-compose up -d --build
    
    print_success "Services started with Docker Compose"
    
    # Show service status
    docker-compose ps
}

# Function to stop services
stop_services() {
    print_status "Stopping MCP TTS services..."
    
    # Stop docker-compose services
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    fi
    
    # Stop standalone container
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
    
    print_success "Services stopped"
}

# Function to show logs
show_logs() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_status "Showing logs for $CONTAINER_NAME..."
        docker logs -f "$CONTAINER_NAME"
    elif [ -f "docker-compose.yml" ]; then
        print_status "Showing Docker Compose logs..."
        docker-compose logs -f
    else
        print_error "No running containers found"
    fi
}

# Function to test the service
test_service() {
    print_status "Testing MCP TTS service..."
    
    # Wait for service to be ready
    sleep 5
    
    # Test if container is running
    if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_error "Container is not running"
        return 1
    fi
    
    # Test health check
    print_status "Running health check..."
    if docker exec "$CONTAINER_NAME" python -c "import sys; sys.path.insert(0, '/app/src'); from mcp_text_to_speech import OfflineTextToSpeechServer; print('Health check passed')"; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi
    
    # Test TTS synthesis
    print_status "Testing TTS synthesis..."
    docker exec "$CONTAINER_NAME" python -m mcp_text_to_speech --info
    
    print_success "Service test completed successfully"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    stop_services
    
    # Remove images
    if docker images -q "$IMAGE_NAME" | grep -q .; then
        print_status "Removing Docker images..."
        docker rmi $(docker images -q "$IMAGE_NAME")
    fi
    
    # Remove volumes
    if docker volume ls -q -f name=tts_cache | grep -q .; then
        print_status "Removing Docker volumes..."
        docker volume rm $(docker volume ls -q -f name=tts_cache)
    fi
    
    # Prune unused resources
    docker system prune -f
    
    print_success "Cleanup completed"
}

# Function to push to registry
push_image() {
    local registry=${1:-"docker.io"}
    local repo=${2:-"yourusername/mcp-text-to-speech"}
    
    print_status "Pushing image to registry: $registry/$repo"
    
    # Tag image for registry
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$registry/$repo:$IMAGE_TAG"
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$registry/$repo:latest"
    
    # Push to registry
    docker push "$registry/$repo:$IMAGE_TAG"
    docker push "$registry/$repo:latest"
    
    print_success "Image pushed to $registry/$repo"
}

# Function to show help
show_help() {
    echo "MCP Text-to-Speech Docker Deployment Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build              Build Docker image"
    echo "  build-multi        Build multi-platform image"
    echo "  run                Run container"
    echo "  compose            Use Docker Compose"
    echo "  stop               Stop all services"
    echo "  logs               Show service logs"
    echo "  test               Test the service"
    echo "  cleanup            Clean up Docker resources"
    echo "  push [registry] [repo]  Push image to registry"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build                    # Build image"
    echo "  $0 run                      # Run container"
    echo "  $0 compose                  # Use Docker Compose"
    echo "  $0 push docker.io myrepo    # Push to Docker Hub"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build_image
            ;;
        build-multi)
            build_multiplatform
            ;;
        run)
            build_image
            run_container
            ;;
        compose)
            compose_up
            ;;
        stop)
            stop_services
            ;;
        logs)
            show_logs
            ;;
        test)
            test_service
            ;;
        cleanup)
            cleanup
            ;;
        push)
            shift
            push_image "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
