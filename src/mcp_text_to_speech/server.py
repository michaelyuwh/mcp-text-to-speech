"""
Local Offline MCP Text-to-Speech Server
Uses multiple TTS engines for completely local speech synthesis
No internet connection or API keys required for basic functionality
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from typing import Any, Optional, List
import io

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest, 
    CallToolResult, 
    ListToolsRequest, 
    ListToolsResult, 
    Tool,
    TextContent,
    JSONRPCMessage,
    ErrorData,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineTextToSpeechServer:
    """MCP server for completely local/offline text-to-speech using multiple engines"""
    
    def __init__(self):
        self.app = Server("mcp-text-to-speech")
        self.available_engines = {}
        self._setup_handlers()
        self._initialize_tts_engines()
    
    def _initialize_tts_engines(self):
        """Initialize available TTS engines"""
        logger.info("🔍 Detecting available TTS engines...")
        
        # Test pyttsx3 (cross-platform offline)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            self.available_engines['pyttsx3'] = {
                'engine': engine,
                'voices': len(voices) if voices else 0,
                'offline': True,
                'quality': 'Good',
                'description': 'Cross-platform offline TTS'
            }
            logger.info("✅ pyttsx3 engine available")
        except Exception as e:
            logger.warning(f"❌ pyttsx3 not available: {e}")
        
        # Test gTTS (Google - requires internet)
        try:
            from gtts import gTTS
            self.available_engines['gtts'] = {
                'module': gTTS,
                'offline': False,
                'quality': 'Excellent',
                'description': 'Google Text-to-Speech (requires internet)'
            }
            logger.info("✅ gTTS engine available")
        except Exception as e:
            logger.warning(f"❌ gTTS not available: {e}")
        
        # Test espeak (Linux offline)
        try:
            import subprocess
            result = subprocess.run(['espeak', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.available_engines['espeak'] = {
                    'offline': True,
                    'quality': 'Basic',
                    'description': 'eSpeak offline TTS (Linux)'
                }
                logger.info("✅ eSpeak engine available")
        except Exception:
            logger.info("ℹ️  eSpeak not available (install with: apt-get install espeak)")
        
        # Test Coqui TTS (AI-based offline)
        try:
            from TTS.api import TTS
            self.available_engines['coqui'] = {
                'module': TTS,
                'offline': True,
                'quality': 'Excellent',
                'description': 'Coqui TTS - AI-based offline synthesis'
            }
            logger.info("✅ Coqui TTS engine available")
        except Exception as e:
            logger.info(f"ℹ️  Coqui TTS not available: {e}")
        
        if not self.available_engines:
            logger.error("❌ No TTS engines available")
        else:
            logger.info(f"🎉 {len(self.available_engines)} TTS engines initialized")
    
    def _setup_handlers(self):
        """Setup MCP message handlers"""
        
        @self.app.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available text-to-speech tools"""
            return [
                Tool(
                    name="get_available_engines",
                    description="Get list of available TTS engines and their capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="synthesize_speech",
                    description="Convert text to speech using specified engine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to convert to speech"
                            },
                            "engine": {
                                "type": "string",
                                "enum": ["pyttsx3", "gtts", "espeak", "coqui", "auto"],
                                "default": "auto",
                                "description": "TTS engine to use"
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice to use (engine-specific)"
                            },
                            "speed": {
                                "type": "number",
                                "default": 150,
                                "description": "Speech speed (words per minute)"
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Output file path (optional, auto-generated if not provided)"
                            },
                            "language": {
                                "type": "string",
                                "default": "en",
                                "description": "Language code (e.g., 'en', 'es', 'fr')"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="list_voices",
                    description="List available voices for specified engine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engine": {
                                "type": "string",
                                "enum": ["pyttsx3", "gtts", "espeak", "coqui"],
                                "default": "pyttsx3",
                                "description": "TTS engine to query"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="play_audio",
                    description="Play generated audio file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to audio file to play"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="batch_synthesize",
                    description="Convert multiple texts to speech files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "texts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of texts to convert"
                            },
                            "engine": {
                                "type": "string",
                                "default": "auto",
                                "description": "TTS engine to use"
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory for audio files"
                            }
                        },
                        "required": ["texts"]
                    }
                )
            ]

        @self.app.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                if name == "get_available_engines":
                    return await self._get_available_engines()
                elif name == "synthesize_speech":
                    return await self._synthesize_speech(arguments)
                elif name == "list_voices":
                    return await self._list_voices(arguments)
                elif name == "play_audio":
                    return await self._play_audio(arguments)
                elif name == "batch_synthesize":
                    return await self._batch_synthesize(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool '{name}': {e}")
                raise Exception(f"Internal error: {str(e)}")
    
    async def _get_available_engines(self) -> list[TextContent]:
        """Get available TTS engines and their capabilities"""
        engines_info = {
            "available_engines": [],
            "total_engines": len(self.available_engines),
            "offline_engines": 0,
            "online_engines": 0
        }
        
        for engine_name, engine_info in self.available_engines.items():
            engine_details = {
                "name": engine_name,
                "offline": engine_info.get('offline', False),
                "quality": engine_info.get('quality', 'Unknown'),
                "description": engine_info.get('description', ''),
                "voices": engine_info.get('voices', 'Unknown')
            }
            engines_info["available_engines"].append(engine_details)
            
            if engine_info.get('offline', False):
                engines_info["offline_engines"] += 1
            else:
                engines_info["online_engines"] += 1
        
        engines_info["recommendation"] = self._get_engine_recommendation()
        
        return [TextContent(type="text", text=json.dumps(engines_info, indent=2))]
    
    def _get_engine_recommendation(self) -> str:
        """Get recommended engine based on available options"""
        if 'pyttsx3' in self.available_engines:
            return "pyttsx3 (best offline option)"
        elif 'espeak' in self.available_engines:
            return "espeak (Linux offline)"
        elif 'coqui' in self.available_engines:
            return "coqui (AI-based offline)"
        elif 'gtts' in self.available_engines:
            return "gtts (requires internet, excellent quality)"
        else:
            return "No engines available"
    
    async def _synthesize_speech(self, arguments: dict) -> list[TextContent]:
        """Synthesize speech from text"""
        text = arguments.get("text", "")
        engine = arguments.get("engine", "auto")
        voice = arguments.get("voice")
        speed = arguments.get("speed", 150)
        output_file = arguments.get("output_file")
        language = arguments.get("language", "en")
        
        if not text:
            raise ValueError("Text is required for synthesis")
        
        # Auto-select engine if not specified
        if engine == "auto":
            engine = self._select_best_engine()
        
        if engine not in self.available_engines:
            raise ValueError(f"Engine '{engine}' not available. Available: {list(self.available_engines.keys())}")
        
        # Generate output file if not provided
        if not output_file:
            output_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex[:8]}.wav")
        
        try:
            if engine == "pyttsx3":
                success = await self._synthesize_pyttsx3(text, output_file, voice, speed, language)
            elif engine == "gtts":
                success = await self._synthesize_gtts(text, output_file, language)
            elif engine == "espeak":
                success = await self._synthesize_espeak(text, output_file, voice, speed)
            elif engine == "coqui":
                success = await self._synthesize_coqui(text, output_file, voice)
            else:
                raise ValueError(f"Synthesis method not implemented for engine: {engine}")
            
            if success:
                file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
                result = {
                    "status": "success",
                    "text": text,
                    "engine": engine,
                    "output_file": output_file,
                    "file_size_bytes": file_size,
                    "language": language,
                    "voice": voice,
                    "speed": speed
                }
                
                logger.info(f"Speech synthesis successful: {output_file} ({file_size} bytes)")
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                raise Exception("Synthesis failed")
                
        except Exception as e:
            logger.error(f"Synthesis error with {engine}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": str(e),
                    "engine": engine,
                    "text": text
                })
            )]
    
    def _select_best_engine(self) -> str:
        """Select the best available engine"""
        if 'pyttsx3' in self.available_engines:
            return 'pyttsx3'
        elif 'coqui' in self.available_engines:
            return 'coqui'
        elif 'espeak' in self.available_engines:
            return 'espeak'
        elif 'gtts' in self.available_engines:
            return 'gtts'
        else:
            raise ValueError("No TTS engines available")
    
    async def _synthesize_pyttsx3(self, text: str, output_file: str, voice: Optional[str], speed: int, language: Optional[str] = None) -> bool:
        """Synthesize using pyttsx3 engine with enhanced Chinese/Cantonese support"""
        try:
            engine = self.available_engines['pyttsx3']['engine']
            
            # Set properties
            engine.setProperty('rate', speed)
            
            # Enhanced Chinese/Cantonese voice selection
            if voice or language:
                voices = engine.getProperty('voices')
                selected_voice = None
                
                # Priority 1: If voice specified, use exact match
                if voice:
                    for v in voices:
                        if voice.lower() in v.name.lower() or voice in v.id:
                            selected_voice = v
                            break
                
                # Priority 2: If language specified, find best Chinese voice
                if not selected_voice and language:
                    lang_lower = language.lower()
                    
                    # Define Chinese language preferences
                    chinese_preferences = {
                        'yue': ['sinji', 'zh_hk'],          # Cantonese preferences
                        'zh-hk': ['sinji', 'zh_hk'],        # Hong Kong
                        'cantonese': ['sinji', 'zh_hk'],    # Cantonese
                        'zh-cn': ['tingting', 'zh_cn'],     # Mandarin (China)
                        'zh-tw': ['meijia', 'zh_tw'],       # Mandarin (Taiwan)
                        'zh': ['tingting', 'zh_cn'],        # Default Chinese
                        'chinese': ['tingting', 'zh_cn']    # Generic Chinese
                    }
                    
                    if lang_lower in chinese_preferences:
                        preferred_voices = chinese_preferences[lang_lower]
                        
                        # Try to find preferred voices in order
                        for pref_voice in preferred_voices:
                            for v in voices:
                                if (pref_voice.lower() in v.name.lower() or 
                                    pref_voice.lower() in v.id.lower()):
                                    selected_voice = v
                                    logger.info(f"Selected {lang_lower} voice: {v.name} ({v.id})")
                                    break
                            if selected_voice:
                                break
                        
                        # Fallback: any Chinese voice
                        if not selected_voice:
                            for v in voices:
                                if ('chinese' in v.name.lower() or 
                                    'zh_' in v.id.lower() or
                                    any(name in v.name.lower() for name in ['tingting', 'sinji', 'meijia'])):
                                    selected_voice = v
                                    logger.info(f"Fallback Chinese voice: {v.name} ({v.id})")
                                    break
                
                # Set the selected voice
                if selected_voice:
                    engine.setProperty('voice', selected_voice.id)
                    logger.info(f"Using voice: {selected_voice.name} ({selected_voice.id})")
            
            # Save to file
            engine.save_to_file(text, output_file)
            engine.runAndWait()
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"pyttsx3 synthesis error: {e}")
            return False
    
    async def _synthesize_gtts(self, text: str, output_file: str, language: str) -> bool:
        """Synthesize using gTTS engine with enhanced Chinese/Cantonese support"""
        try:
            from gtts import gTTS
            
            # Map common Chinese variants to supported gTTS codes
            language_map = {
                'zh-hk': 'yue',        # Hong Kong -> Cantonese
                'zh-yue': 'yue',       # Yue -> Cantonese  
                'cantonese': 'yue',    # Cantonese -> yue
                'zh-cn': 'zh-CN',      # Simplified Chinese
                'zh-tw': 'zh-TW',      # Traditional Chinese
                'zh': 'zh',            # Mandarin Chinese
                'chinese': 'zh'        # Default Chinese -> Mandarin
            }
            
            # Use mapped language or original if not found
            gtts_lang = language_map.get(language.lower(), language)
            
            logger.info(f"Using gTTS language: {gtts_lang} (from input: {language})")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(output_file)
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"gTTS synthesis error: {e}")
            return False
    
    async def _synthesize_espeak(self, text: str, output_file: str, voice: Optional[str], speed: int) -> bool:
        """Synthesize using eSpeak engine"""
        try:
            import subprocess
            
            cmd = ['espeak', '-s', str(speed), '-w', output_file]
            
            if voice:
                cmd.extend(['-v', voice])
            
            cmd.append(text)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"eSpeak synthesis error: {e}")
            return False
    
    async def _synthesize_coqui(self, text: str, output_file: str, voice: Optional[str]) -> bool:
        """Synthesize using Coqui TTS engine"""
        try:
            from TTS.api import TTS
            
            # Use a default model if none specified
            model_name = voice or "tts_models/en/ljspeech/tacotron2-DDC"
            
            tts = TTS(model_name=model_name)
            tts.tts_to_file(text=text, file_path=output_file)
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"Coqui TTS synthesis error: {e}")
            return False
    
    async def _list_voices(self, arguments: dict) -> list[TextContent]:
        """List available voices for specified engine"""
        engine = arguments.get("engine", "pyttsx3")
        
        if engine not in self.available_engines:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Engine '{engine}' not available",
                    "available_engines": list(self.available_engines.keys())
                })
            )]
        
        voices_info = {"engine": engine, "voices": []}
        
        try:
            if engine == "pyttsx3":
                engine_obj = self.available_engines['pyttsx3']['engine']
                voices = engine_obj.getProperty('voices')
                for voice in voices:
                    voices_info["voices"].append({
                        "id": voice.id,
                        "name": voice.name,
                        "languages": getattr(voice, 'languages', ['unknown'])
                    })
            
            elif engine == "gtts":
                # gTTS supports many languages including enhanced Chinese/Cantonese
                voices_info["voices"] = [
                    {"id": "en", "name": "English", "languages": ["en"]},
                    {"id": "es", "name": "Spanish", "languages": ["es"]},
                    {"id": "fr", "name": "French", "languages": ["fr"]},
                    {"id": "de", "name": "German", "languages": ["de"]},
                    {"id": "it", "name": "Italian", "languages": ["it"]},
                    {"id": "zh", "name": "Chinese (Mandarin)", "languages": ["zh"]},
                    {"id": "zh-CN", "name": "Chinese (Simplified)", "languages": ["zh-CN"]},
                    {"id": "zh-TW", "name": "Chinese (Traditional)", "languages": ["zh-TW"]},
                    {"id": "yue", "name": "Cantonese (粵語)", "languages": ["yue", "zh-HK"]},
                    {"id": "ja", "name": "Japanese", "languages": ["ja"]},
                    {"id": "ko", "name": "Korean", "languages": ["ko"]}
                ]
            
            elif engine == "espeak":
                # eSpeak has many voices
                import subprocess
                result = subprocess.run(['espeak', '--voices'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 4:
                            voices_info["voices"].append({
                                "id": parts[4],
                                "name": parts[3],
                                "languages": [parts[1]]
                            })
            
            voices_info["total_voices"] = len(voices_info["voices"])
            
        except Exception as e:
            voices_info["error"] = str(e)
        
        return [TextContent(type="text", text=json.dumps(voices_info, indent=2))]
    
    async def _play_audio(self, arguments: dict) -> list[TextContent]:
        """Play generated audio file"""
        file_path = arguments.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "File not found",
                    "file_path": file_path
                })
            )]
        
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            result = {
                "status": "success",
                "message": "Audio played successfully",
                "file_path": file_path
            }
            
        except Exception as e:
            result = {
                "status": "error",
                "message": str(e),
                "file_path": file_path
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _batch_synthesize(self, arguments: dict) -> list[TextContent]:
        """Convert multiple texts to speech files"""
        texts = arguments.get("texts", [])
        engine = arguments.get("engine", "auto")
        output_dir = arguments.get("output_dir", tempfile.gettempdir())
        
        if not texts:
            raise ValueError("At least one text is required")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for i, text in enumerate(texts):
            output_file = os.path.join(output_dir, f"batch_tts_{i+1:03d}_{uuid.uuid4().hex[:8]}.wav")
            
            # Use single synthesis for each text
            synthesis_result = await self._synthesize_speech({
                "text": text,
                "engine": engine,
                "output_file": output_file
            })
            
            result_data = json.loads(synthesis_result[0].text)
            results.append(result_data)
        
        batch_result = {
            "status": "completed",
            "total_files": len(texts),
            "output_directory": output_dir,
            "results": results
        }
        
        return [TextContent(type="text", text=json.dumps(batch_result, indent=2))]

    async def run_server(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-text-to-speech",
                    server_version="1.0.0",
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

# Entry point for running the server
async def main():
    """Main entry point"""
    server = OfflineTextToSpeechServer()
    await server.run_server()

if __name__ == "__main__":
    asyncio.run(main())
