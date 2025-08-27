# MCP Text-to-Speech Server

A powerful, offline-first **Text-to-Speech (TTS) MCP server** that works completely locally without requiring internet connectivity or API keys. Perfect for privacy-conscious applications, development environments, and production deployments where data sovereignty is important.

## 🎯 Key Features

- **🔒 Completely Offline**: Works without internet connection using local TTS engines
- **🌐 Online Fallback**: Supports cloud TTS services when needed
- **🤖 Multiple Engines**: pyttsx3, espeak, festival, Coqui TTS, gTTS, Azure, Polly, Watson
- **🚀 Auto-Detection**: Automatically selects the best available TTS engine
- **🐳 Docker Ready**: Optimized multi-platform Docker containers
- **🎵 Multiple Formats**: Supports WAV, MP3, and other audio formats
- **🌍 Multi-Language**: Supports dozens of languages and accents
- **⚡ High Performance**: Optimized for speed and low resource usage
- **🔧 Easy Integration**: Simple MCP protocol integration

## 🛠️ Supported TTS Engines

### Offline Engines (No Internet Required)
- **pyttsx3**: Cross-platform offline TTS with system voices
- **espeak**: Lightweight, open-source TTS for Linux
- **festival**: High-quality speech synthesis for Linux
- **Coqui TTS**: AI-based neural TTS with excellent quality

### Online Services (Internet Required)
- **Google TTS (gTTS)**: Free, high-quality synthesis
- **Azure Cognitive Services**: Premium neural voices
- **Amazon Polly**: Professional-grade TTS with neural voices
- **IBM Watson**: Enterprise-level speech synthesis

## 📦 Quick Start

### Option 1: Python Installation (Recommended for Development)

```bash
# Clone the repository
git clone <repository-url>
cd mcp-text-to-speech

# Install with uv (recommended)
pip install uv
uv pip install .

# Or install with pip
pip install .

# Run with auto-detection
python -m mcp_text_to_speech

# Check available engines
python -m mcp_text_to_speech --info
```

### Option 2: Docker (Recommended for Production)

```bash
# Quick start with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t mcp-text-to-speech .
docker run -it --rm \
  -v ./output:/app/output \
  --device /dev/snd:/dev/snd \
  mcp-text-to-speech
```

### Option 3: Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd mcp-text-to-speech

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install in development mode
pip install -e ".[dev]"

# Install offline TTS engines
sudo apt-get install espeak festival  # Linux
# On macOS: brew install espeak festival

# Run development server
python -m mcp_text_to_speech --debug
```

## 🎛️ Usage Examples

### Basic Text-to-Speech

```python
# Using MCP protocol
{
  "method": "tools/call",
  "params": {
    "name": "synthesize_speech",
    "arguments": {
      "text": "Hello, this is a test of text-to-speech synthesis!",
      "engine": "auto",
      "language": "en"
    }
  }
}
```

### Advanced Configuration

```python
# High-quality synthesis with specific voice
{
  "method": "tools/call",
  "params": {
    "name": "synthesize_speech",
    "arguments": {
      "text": "Welcome to our application",
      "engine": "pyttsx3",
      "voice": "female",
      "speed": 180,
      "language": "en",
      "output_file": "/app/output/welcome.wav"
    }
  }
}
```

### Batch Processing

```python
# Convert multiple texts at once
{
  "method": "tools/call",
  "params": {
    "name": "batch_synthesize",
    "arguments": {
      "texts": [
        "Welcome to our service",
        "Please select an option",
        "Thank you for your choice"
      ],
      "engine": "auto",
      "output_dir": "/app/output/batch"
    }
  }
}
```

## 🌍 Language Support

### **Enhanced Chinese & Cantonese Support** 🇭🇰
Perfect for Hong Kong users and Cantonese speakers:

#### **Cantonese (粵語)**
- **Offline**: macOS Sinji voice (`zh-HK`) - Native Hong Kong Cantonese
- **Online**: gTTS Cantonese (`yue`) - High-quality synthesis
- **Smart Mapping**: `zh-HK`, `cantonese` → Auto-selects best Cantonese voice

#### **Mandarin Chinese (普通話)**
- **Simplified Chinese**: `zh-CN` - Mainland China
- **Traditional Chinese**: `zh-TW` - Taiwan  
- **Generic Chinese**: `zh` - Default Mandarin

#### **Language Usage Examples**
```python
# Hong Kong Cantonese (Offline)
{"language": "zh-HK", "engine": "pyttsx3"}  # → Sinji voice

# Cantonese (Online)  
{"language": "yue", "engine": "gtts"}       # → gTTS Cantonese

# Auto-detection
{"language": "cantonese", "engine": "auto"} # → Best available
```

### **Other Supported Languages**
The server supports numerous languages depending on the engine:

- **English**: en, en-US, en-GB, en-AU
- **Spanish**: es, es-ES, es-MX, es-AR
- **French**: fr, fr-FR, fr-CA
- **German**: de, de-DE, de-AT
- **Italian**: it, it-IT
- **Portuguese**: pt, pt-PT, pt-BR
- **Russian**: ru
- **Japanese**: ja
- **Korean**: ko
- **Chinese**: zh, zh-CN, zh-TW, yue (Cantonese)
- **And many more...**

## ⚙️ Configuration

### Environment Variables

```bash
# Force specific mode
export TTS_MODE=offline  # or 'online' or 'auto'

# Cache and output directories
export TTS_CACHE_DIR=/tmp/tts_cache
export TTS_OUTPUT_DIR=/app/output

# Online service credentials (optional)
export AZURE_SPEECH_KEY=your_key
export AZURE_SPEECH_REGION=eastus
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export IBM_WATSON_APIKEY=your_key
export IBM_WATSON_URL=your_url
```

### Command Line Options

```bash
# Auto-detection (default)
python -m mcp_text_to_speech

# Force offline mode
python -m mcp_text_to_speech --offline

# Force online mode
python -m mcp_text_to_speech --online

# Show environment info
python -m mcp_text_to_speech --info

# Debug mode with detailed logging
python -m mcp_text_to_speech --debug
```

## 🐳 Docker Deployment

### Production Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-tts:
    image: mcp-text-to-speech:latest
    restart: unless-stopped
    volumes:
      - ./output:/app/output
      - tts_cache:/tmp/tts_cache
    environment:
      - TTS_MODE=offline
    devices:
      - /dev/snd:/dev/snd
    ports:
      - "8000:8000"
```

### Multi-Platform Build

```bash
# Build for multiple architectures
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t mcp-text-to-speech:latest .
```

## 🛠️ Available MCP Tools

### 1. `get_available_engines`
Get list of available TTS engines and their capabilities.

### 2. `synthesize_speech`
Convert text to speech with customizable options:
- Text content
- Engine selection
- Voice selection
- Speed/rate control
- Language selection
- Output format

### 3. `list_voices`
List available voices for each engine with details:
- Voice IDs and names
- Supported languages
- Gender information

### 4. `play_audio`
Play generated audio files through the system audio.

### 5. `batch_synthesize`
Convert multiple texts to speech files efficiently.

### 6. Online Service Tools
- `get_available_services`: List online TTS services
- `synthesize_speech_online`: Use cloud TTS services
- `list_online_voices`: Browse cloud voice options
- `get_service_limits`: Check API usage and limits

## 🔧 System Requirements

### Minimum Requirements
- Python 3.9+
- 512MB RAM
- 100MB disk space
- Audio output capability

### Recommended for Production
- Python 3.11+
- 1GB RAM
- 1GB disk space
- Linux with audio system (ALSA/PulseAudio)

### Dependencies

**Core Dependencies:**
- `mcp` >= 1.0.0
- `pyttsx3` >= 2.90 (cross-platform TTS)
- `pygame` >= 2.0.0 (audio playback)

**Optional TTS Engines:**
- `gtts` >= 2.3.0 (Google TTS)
- `TTS` >= 0.22.0 (Coqui AI TTS)
- `azure-cognitiveservices-speech` (Azure)
- `boto3` (Amazon Polly)
- `ibm-watson` (IBM Watson)

**System Dependencies (Linux):**
```bash
sudo apt-get install espeak festival alsa-utils pulseaudio sox ffmpeg
```

## 🚀 Performance Optimization

### Speed Optimizations
- **Engine Selection**: pyttsx3 for speed, Coqui for quality
- **Caching**: Automatic caching of generated audio
- **Batch Processing**: Efficient multi-text synthesis
- **Resource Management**: Memory-efficient streaming

### Resource Usage
- **Offline Mode**: ~100-500MB RAM
- **Online Mode**: ~50-200MB RAM
- **Disk Cache**: ~10MB per hour of audio
- **CPU**: Low usage except during synthesis

## 🔍 Troubleshooting

### Common Issues

**No TTS engines available:**
```bash
# Install offline engines
pip install pyttsx3 gtts
sudo apt-get install espeak  # Linux

# Check environment
python -m mcp_text_to_speech --info
```

**Audio playback issues:**
```bash
# Check audio system
pulseaudio --check -v
aplay -l

# Configure Docker audio
docker run --device /dev/snd:/dev/snd mcp-text-to-speech
```

**Online service errors:**
```bash
# Check credentials
export AZURE_SPEECH_KEY=your_key
export AZURE_SPEECH_REGION=your_region

# Test connectivity
python -c "from gtts import gTTS; print('gTTS works')"
```

### Debug Mode

```bash
# Run with detailed logging
python -m mcp_text_to_speech --debug

# Check specific engine
python -c "import pyttsx3; engine = pyttsx3.init(); print('pyttsx3 works')"
```

## 🤝 Integration Examples

### n8n Integration

```javascript
// n8n workflow node
{
  "nodes": [
    {
      "name": "Text to Speech",
      "type": "mcp-text-to-speech",
      "parameters": {
        "text": "{{ $json.message }}",
        "engine": "auto",
        "language": "en"
      }
    }
  ]
}
```

### Claude Desktop Integration

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "text-to-speech": {
      "command": "python",
      "args": ["-m", "mcp_text_to_speech"],
      "cwd": "/path/to/mcp-text-to-speech"
    }
  }
}
```

## 🔒 Privacy & Security

- **Data Privacy**: All text processing happens locally
- **No Telemetry**: No data sent to external services (offline mode)
- **Secure Defaults**: Non-root Docker containers
- **Credential Management**: Environment-based configuration
- **Audit Trail**: Comprehensive logging available

## 📊 Benchmarks

| Engine | Quality | Speed | Memory | Offline |
|--------|---------|-------|--------|---------|
| pyttsx3 | Good | Fast | 100MB | ✅ |
| espeak | Basic | Very Fast | 50MB | ✅ |
| Coqui TTS | Excellent | Medium | 500MB | ✅ |
| gTTS | Excellent | Fast | 100MB | ❌ |
| Azure | Excellent | Fast | 150MB | ❌ |

## 🗺️ Roadmap

- [ ] **WebRTC Integration**: Real-time streaming synthesis
- [ ] **Voice Cloning**: Custom voice model support
- [ ] **SSML Support**: Advanced speech markup language
- [ ] **Emotion Control**: Emotional expression in synthesis
- [ ] **Multilingual Models**: Advanced language switching
- [ ] **Performance Dashboard**: Real-time monitoring
- [ ] **Plugin System**: Custom engine integration

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/mcp-text-to-speech.git
cd mcp-text-to-speech

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [pyttsx3](https://pypi.org/project/pyttsx3/) - Cross-platform TTS library
- [gTTS](https://pypi.org/project/gTTS/) - Google Text-to-Speech wrapper
- [Coqui TTS](https://github.com/coqui-ai/TTS) - Advanced neural TTS
- [MCP Protocol](https://modelcontextprotocol.io/) - Model Context Protocol specification
- [espeak](http://espeak.sourceforge.net/) - Compact open source TTS
- [Festival](http://www.cstr.ed.ac.uk/projects/festival/) - Speech synthesis system

## 🆘 Support

- **Documentation**: [Full documentation](https://yourusername.github.io/mcp-text-to-speech/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-text-to-speech/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mcp-text-to-speech/discussions)
- **Email**: support@yourcompany.com

---

**Made with ❤️ for the MCP community**
