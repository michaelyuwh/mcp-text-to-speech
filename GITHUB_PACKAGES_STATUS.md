# 📦 GitHub Packages Status & Manual Setup Guide

## 🎯 Current Status

### ✅ What's Ready:
- GitHub Actions workflows are deployed to both repositories
- Docker images are built and tagged locally for GitHub Container Registry
- Tags `v1.2.0-packages` have been pushed to trigger automated builds

### 🔄 GitHub Actions Status:
The workflows should be running now. Check:
- **Text-to-Speech**: https://github.com/michaelyuwh/mcp-text-to-speech/actions
- **Speech-to-Text**: https://github.com/michaelyuwh/mcp-speech-to-text/actions

## 🚀 Manual Push Instructions (If Needed)

If GitHub Actions doesn't complete or you want to push manually:

### 1. Create GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `write:packages`
   - ✅ `read:packages`
   - ✅ `delete:packages` (optional)
4. Copy the token

### 2. Login to GitHub Container Registry
```bash
# Replace YOUR_TOKEN with your actual token
echo "YOUR_TOKEN" | docker login ghcr.io -u michaelyuwh --password-stdin
```

### 3. Push Images Manually
```bash
# Text-to-Speech
docker push ghcr.io/michaelyuwh/mcp-text-to-speech:slim
docker push ghcr.io/michaelyuwh/mcp-text-to-speech:v1.1.0-slim
docker push ghcr.io/michaelyuwh/mcp-text-to-speech:latest

# Speech-to-Text  
docker push ghcr.io/michaelyuwh/mcp-speech-to-text:slim
docker push ghcr.io/michaelyuwh/mcp-speech-to-text:v1.1.0-slim
docker push ghcr.io/michaelyuwh/mcp-speech-to-text:latest
```

## 🔍 Verify Package Availability

Once published, packages will be visible at:
- **Text-to-Speech**: https://github.com/michaelyuwh/mcp-text-to-speech/pkgs/container/mcp-text-to-speech
- **Speech-to-Text**: https://github.com/michaelyuwh/mcp-speech-to-text/pkgs/container/mcp-speech-to-text

## 🎯 Pull Commands (Once Available)

```bash
# Text-to-Speech from GitHub Packages
docker pull ghcr.io/michaelyuwh/mcp-text-to-speech:slim
docker pull ghcr.io/michaelyuwh/mcp-text-to-speech:v1.2.0-packages

# Speech-to-Text from GitHub Packages
docker pull ghcr.io/michaelyuwh/mcp-speech-to-text:slim  
docker pull ghcr.io/michaelyuwh/mcp-speech-to-text:v1.2.0-packages
```

## 🔧 Troubleshooting

### Issue: "Package not found"
**Solution**: 
1. Check GitHub Actions completed successfully
2. Verify repository visibility (packages inherit repo visibility)
3. Ensure authentication if repository is private

### Issue: "Authentication required"  
**Solution**:
```bash
# Login first
docker login ghcr.io -u YOUR_USERNAME
# Then pull
docker pull ghcr.io/michaelyuwh/mcp-text-to-speech:slim
```

### Issue: "GitHub Actions failed"
**Solution**:
1. Check workflow logs at: https://github.com/michaelyuwh/mcp-text-to-speech/actions
2. Verify Dockerfile.slim exists in repository
3. Check for any build errors

## 📊 Expected Timeline
- **GitHub Actions**: 3-5 minutes to complete
- **Package visibility**: Immediate after successful push
- **Public availability**: Depends on repository visibility settings
