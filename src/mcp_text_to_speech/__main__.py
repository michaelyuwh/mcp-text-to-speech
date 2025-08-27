"""
MCP Text-to-Speech Server with Auto-Detection
Automatically selects the best available TTS engine/service based on the environment
Falls back gracefully from offline engines to online services
"""

import asyncio
import logging
import os
import sys
import subprocess
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_platform() -> str:
    """Detect the current platform and architecture"""
    import platform
    
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    platform_info = f"{system}-{machine}"
    logger.info(f"🔍 Detected platform: {platform_info}")
    
    return platform_info

def check_offline_tts_engines() -> dict:
    """Check which offline TTS engines are available"""
    engines = {}
    
    # Check pyttsx3 (cross-platform)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engines['pyttsx3'] = {
            'available': True,
            'voices': len(voices) if voices else 0,
            'platform': 'cross-platform'
        }
        logger.info("✅ pyttsx3 available")
    except Exception as e:
        logger.info(f"❌ pyttsx3 not available: {e}")
        engines['pyttsx3'] = {'available': False, 'error': str(e)}
    
    # Check espeak (Linux)
    try:
        result = subprocess.run(['espeak', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            engines['espeak'] = {
                'available': True,
                'version': result.stdout.strip().split('\n')[0],
                'platform': 'linux'
            }
            logger.info("✅ espeak available")
        else:
            engines['espeak'] = {'available': False, 'error': 'Command failed'}
    except Exception as e:
        engines['espeak'] = {'available': False, 'error': str(e)}
    
    # Check festival (Linux)
    try:
        result = subprocess.run(['festival', '--version'], 
                              capture_output=True, text=True, timeout=5)
        engines['festival'] = {
            'available': result.returncode == 0,
            'platform': 'linux'
        }
        if result.returncode == 0:
            logger.info("✅ festival available")
    except Exception as e:
        engines['festival'] = {'available': False, 'error': str(e)}
    
    # Check Coqui TTS
    try:
        from TTS.api import TTS
        engines['coqui'] = {
            'available': True,
            'platform': 'cross-platform',
            'ai_models': True
        }
        logger.info("✅ Coqui TTS available")
    except Exception as e:
        engines['coqui'] = {'available': False, 'error': str(e)}
    
    return engines

def check_online_tts_services() -> dict:
    """Check which online TTS services are available"""
    services = {}
    
    # Check gTTS
    try:
        from gtts import gTTS
        services['gtts'] = {
            'available': True,
            'free': True,
            'quality': 'good'
        }
        logger.info("✅ gTTS available")
    except Exception as e:
        services['gtts'] = {'available': False, 'error': str(e)}
    
    # Check Azure Speech Services
    try:
        import azure.cognitiveservices.speech as speechsdk
        has_credentials = (os.getenv('AZURE_SPEECH_KEY') and 
                          os.getenv('AZURE_SPEECH_REGION'))
        services['azure'] = {
            'available': has_credentials,
            'module_installed': True,
            'credentials_configured': has_credentials,
            'quality': 'excellent'
        }
        if has_credentials:
            logger.info("✅ Azure Speech Services available")
        else:
            logger.info("ℹ️  Azure Speech Services: credentials not configured")
    except Exception as e:
        services['azure'] = {
            'available': False, 
            'module_installed': False,
            'error': str(e)
        }
    
    # Check Amazon Polly
    try:
        import boto3
        has_credentials = (os.getenv('AWS_ACCESS_KEY_ID') and 
                          os.getenv('AWS_SECRET_ACCESS_KEY'))
        services['polly'] = {
            'available': has_credentials,
            'module_installed': True,
            'credentials_configured': has_credentials,
            'quality': 'excellent'
        }
        if has_credentials:
            logger.info("✅ Amazon Polly available")
        else:
            logger.info("ℹ️  Amazon Polly: AWS credentials not configured")
    except Exception as e:
        services['polly'] = {
            'available': False,
            'module_installed': False, 
            'error': str(e)
        }
    
    # Check IBM Watson
    try:
        from ibm_watson import TextToSpeechV1
        has_credentials = (os.getenv('IBM_WATSON_APIKEY') and 
                          os.getenv('IBM_WATSON_URL'))
        services['watson'] = {
            'available': has_credentials,
            'module_installed': True,
            'credentials_configured': has_credentials,
            'quality': 'excellent'
        }
        if has_credentials:
            logger.info("✅ IBM Watson TTS available")
        else:
            logger.info("ℹ️  IBM Watson: credentials not configured")
    except Exception as e:
        services['watson'] = {
            'available': False,
            'module_installed': False,
            'error': str(e)
        }
    
    return services

def select_best_server() -> str:
    """Select the best available TTS server based on environment"""
    platform = detect_platform()
    offline_engines = check_offline_tts_engines()
    online_services = check_online_tts_services()
    
    # Count available options
    available_offline = sum(1 for engine in offline_engines.values() 
                           if engine.get('available', False))
    available_online = sum(1 for service in online_services.values() 
                          if service.get('available', False))
    
    logger.info(f"📊 Available engines: {available_offline} offline, {available_online} online")
    
    # Decision logic: prefer offline engines for privacy and no API costs
    if available_offline > 0:
        logger.info("🎯 Using offline TTS server (privacy-focused, no API costs)")
        
        # Prefer high-quality offline engines
        if offline_engines.get('coqui', {}).get('available', False):
            logger.info("🚀 Selected Coqui TTS (AI-based, excellent quality)")
        elif offline_engines.get('pyttsx3', {}).get('available', False):
            logger.info("🚀 Selected pyttsx3 (cross-platform, good quality)")
        elif offline_engines.get('espeak', {}).get('available', False):
            logger.info("🚀 Selected espeak (Linux native, basic quality)")
        
        return "offline"
    
    elif available_online > 0:
        logger.info("🌐 Using online TTS server (requires internet)")
        
        # Prefer free online services
        if online_services.get('gtts', {}).get('available', False):
            logger.info("🚀 Selected Google TTS (free, good quality)")
        elif online_services.get('azure', {}).get('available', False):
            logger.info("🚀 Selected Azure Speech (paid, excellent quality)")
        elif online_services.get('polly', {}).get('available', False):
            logger.info("🚀 Selected Amazon Polly (paid, excellent quality)")
        elif online_services.get('watson', {}).get('available', False):
            logger.info("🚀 Selected IBM Watson (paid, excellent quality)")
        
        return "online"
    
    else:
        logger.error("❌ No TTS engines or services available!")
        logger.error("💡 Install dependencies: pip install pyttsx3 gtts")
        logger.error("💡 Or configure cloud service credentials")
        return "none"

def print_environment_info():
    """Print detailed environment information"""
    platform = detect_platform()
    offline_engines = check_offline_tts_engines()
    online_services = check_online_tts_services()
    
    print("\n" + "="*60)
    print("🎤 MCP Text-to-Speech Server - Environment Analysis")
    print("="*60)
    
    print(f"\n🖥️  Platform: {platform}")
    
    print("\n🔧 Offline TTS Engines:")
    for engine, info in offline_engines.items():
        status = "✅" if info.get('available', False) else "❌"
        platform_info = info.get('platform', 'unknown')
        print(f"   {status} {engine} ({platform_info})")
        if not info.get('available', False):
            print(f"      Error: {info.get('error', 'Unknown')}")
        elif engine == 'pyttsx3' and 'voices' in info:
            print(f"      Voices: {info['voices']}")
    
    print("\n🌐 Online TTS Services:")
    for service, info in online_services.items():
        status = "✅" if info.get('available', False) else "❌"
        quality = info.get('quality', 'unknown')
        print(f"   {status} {service} ({quality} quality)")
        if not info.get('available', False):
            if not info.get('module_installed', True):
                print(f"      Module not installed: {info.get('error', '')}")
            elif not info.get('credentials_configured', True):
                print(f"      Credentials not configured")
    
    available_offline = sum(1 for engine in offline_engines.values() 
                           if engine.get('available', False))
    available_online = sum(1 for service in online_services.values() 
                          if service.get('available', False))
    
    print(f"\n📊 Summary: {available_offline} offline engines, {available_online} online services")
    
    if available_offline == 0 and available_online == 0:
        print("\n❌ No TTS engines available!")
        print("💡 Quick setup:")
        print("   pip install pyttsx3 gtts")
        print("   # For advanced AI voices:")
        print("   pip install TTS")
    
    print("="*60 + "\n")

async def run_offline_server():
    """Run the offline TTS server"""
    try:
        from .server import OfflineTextToSpeechServer
        server = OfflineTextToSpeechServer()
        await server.run_server()
    except ImportError as e:
        logger.error(f"Failed to import offline server: {e}")
        raise

async def run_online_server():
    """Run the online TTS server"""
    try:
        from .server_online import OnlineTextToSpeechServer
        server = OnlineTextToSpeechServer()
        await server.run_server()
    except ImportError as e:
        logger.error(f"Failed to import online server: {e}")
        raise

async def main():
    """Main entry point with auto-detection"""
    
    # Check for debug flag
    if "--debug" in sys.argv or "-d" in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
        print_environment_info()
    
    # Check for info flag
    if "--info" in sys.argv or "-i" in sys.argv:
        print_environment_info()
        return
    
    # Check for force flags
    if "--offline" in sys.argv:
        logger.info("🔧 Force offline mode requested")
        await run_offline_server()
        return
    
    if "--online" in sys.argv:
        logger.info("🔧 Force online mode requested") 
        await run_online_server()
        return
    
    # Auto-detect best server
    logger.info("🔍 Auto-detecting best TTS server...")
    server_type = select_best_server()
    
    if server_type == "offline":
        await run_offline_server()
    elif server_type == "online":
        await run_online_server()
    else:
        logger.error("❌ No TTS servers available")
        print_environment_info()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server crashed: {e}")
        sys.exit(1)
