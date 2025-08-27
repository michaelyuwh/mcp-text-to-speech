"""
Online TTS MCP Server (Fallback)
Uses cloud-based TTS services when offline engines are not available
Includes gTTS, Azure Cognitive Services, and other online providers
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from typing import Any, Optional, List

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

class OnlineTextToSpeechServer:
    """MCP server for online/cloud-based text-to-speech services"""
    
    def __init__(self):
        self.app = Server("mcp-text-to-speech-online")
        self.available_services = {}
        self._setup_handlers()
        self._initialize_online_services()
    
    def _initialize_online_services(self):
        """Initialize available online TTS services"""
        logger.info("🔍 Detecting available online TTS services...")
        
        # Test gTTS (Google)
        try:
            from gtts import gTTS
            self.available_services['gtts'] = {
                'module': gTTS,
                'languages': ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'],
                'quality': 'Excellent',
                'description': 'Google Text-to-Speech',
                'free': True
            }
            logger.info("✅ Google TTS (gTTS) available")
        except Exception as e:
            logger.warning(f"❌ Google TTS not available: {e}")
        
        # Test Azure Cognitive Services
        try:
            import azure.cognitiveservices.speech as speechsdk
            if os.getenv('AZURE_SPEECH_KEY') and os.getenv('AZURE_SPEECH_REGION'):
                self.available_services['azure'] = {
                    'module': speechsdk,
                    'quality': 'Excellent',
                    'description': 'Azure Cognitive Services Speech',
                    'neural_voices': True,
                    'free': False
                }
                logger.info("✅ Azure Speech Services available")
            else:
                logger.info("ℹ️  Azure Speech Services: Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables")
        except Exception:
            logger.info("ℹ️  Azure Speech Services not available (install with: pip install azure-cognitiveservices-speech)")
        
        # Test Amazon Polly
        try:
            import boto3
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                self.available_services['polly'] = {
                    'client': boto3.client('polly'),
                    'quality': 'Excellent',
                    'description': 'Amazon Polly',
                    'neural_voices': True,
                    'free': False
                }
                logger.info("✅ Amazon Polly available")
            else:
                logger.info("ℹ️  Amazon Polly: Set AWS credentials in environment variables")
        except Exception:
            logger.info("ℹ️  Amazon Polly not available (install with: pip install boto3)")
        
        # Test IBM Watson
        try:
            from ibm_watson import TextToSpeechV1
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            
            if os.getenv('IBM_WATSON_APIKEY') and os.getenv('IBM_WATSON_URL'):
                authenticator = IAMAuthenticator(os.getenv('IBM_WATSON_APIKEY'))
                tts = TextToSpeechV1(authenticator=authenticator)
                tts.set_service_url(os.getenv('IBM_WATSON_URL'))
                
                self.available_services['watson'] = {
                    'client': tts,
                    'quality': 'Excellent',
                    'description': 'IBM Watson Text to Speech',
                    'free': False
                }
                logger.info("✅ IBM Watson TTS available")
            else:
                logger.info("ℹ️  IBM Watson: Set IBM_WATSON_APIKEY and IBM_WATSON_URL environment variables")
        except Exception:
            logger.info("ℹ️  IBM Watson not available (install with: pip install ibm-watson)")
        
        if not self.available_services:
            logger.error("❌ No online TTS services available")
        else:
            logger.info(f"🎉 {len(self.available_services)} online TTS services initialized")
    
    def _setup_handlers(self):
        """Setup MCP message handlers"""
        
        @self.app.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available online text-to-speech tools"""
            return [
                Tool(
                    name="get_available_services",
                    description="Get list of available online TTS services",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="synthesize_speech_online",
                    description="Convert text to speech using online services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to convert to speech"
                            },
                            "service": {
                                "type": "string",
                                "enum": ["gtts", "azure", "polly", "watson", "auto"],
                                "default": "auto",
                                "description": "Online TTS service to use"
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice to use (service-specific)"
                            },
                            "language": {
                                "type": "string",
                                "default": "en",
                                "description": "Language code"
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Output file path"
                            },
                            "speed": {
                                "type": "string",
                                "enum": ["x-slow", "slow", "medium", "fast", "x-fast"],
                                "default": "medium",
                                "description": "Speech speed"
                            },
                            "pitch": {
                                "type": "string",
                                "enum": ["x-low", "low", "medium", "high", "x-high"],
                                "default": "medium",
                                "description": "Speech pitch"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="list_online_voices",
                    description="List available voices for online services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "enum": ["gtts", "azure", "polly", "watson"],
                                "default": "gtts",
                                "description": "Online service to query"
                            },
                            "language": {
                                "type": "string",
                                "default": "en",
                                "description": "Language to filter voices"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_service_limits",
                    description="Get usage limits and pricing for online services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "description": "Service to check limits for"
                            }
                        },
                        "required": []
                    }
                )
            ]

        @self.app.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                if name == "get_available_services":
                    return await self._get_available_services()
                elif name == "synthesize_speech_online":
                    return await self._synthesize_speech_online(arguments)
                elif name == "list_online_voices":
                    return await self._list_online_voices(arguments)
                elif name == "get_service_limits":
                    return await self._get_service_limits(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool '{name}': {e}")
                raise Exception(f"Internal error: {str(e)}")
    
    async def _get_available_services(self) -> list[TextContent]:
        """Get available online TTS services"""
        services_info = {
            "available_services": [],
            "total_services": len(self.available_services),
            "free_services": 0,
            "paid_services": 0
        }
        
        for service_name, service_info in self.available_services.items():
            service_details = {
                "name": service_name,
                "quality": service_info.get('quality', 'Unknown'),
                "description": service_info.get('description', ''),
                "free": service_info.get('free', False),
                "neural_voices": service_info.get('neural_voices', False),
                "languages": service_info.get('languages', 'Multiple')
            }
            services_info["available_services"].append(service_details)
            
            if service_info.get('free', False):
                services_info["free_services"] += 1
            else:
                services_info["paid_services"] += 1
        
        services_info["recommendation"] = self._get_service_recommendation()
        
        return [TextContent(type="text", text=json.dumps(services_info, indent=2))]
    
    def _get_service_recommendation(self) -> str:
        """Get recommended service"""
        if 'gtts' in self.available_services:
            return "gtts (free, good quality)"
        elif 'azure' in self.available_services:
            return "azure (excellent quality, neural voices)"
        elif 'polly' in self.available_services:
            return "polly (excellent quality, many voices)"
        elif 'watson' in self.available_services:
            return "watson (excellent quality)"
        else:
            return "No services available"
    
    async def _synthesize_speech_online(self, arguments: dict) -> list[TextContent]:
        """Synthesize speech using online services"""
        text = arguments.get("text", "")
        service = arguments.get("service", "auto")
        voice = arguments.get("voice")
        language = arguments.get("language", "en")
        output_file = arguments.get("output_file")
        speed = arguments.get("speed", "medium")
        pitch = arguments.get("pitch", "medium")
        
        if not text:
            raise ValueError("Text is required for synthesis")
        
        # Auto-select service
        if service == "auto":
            service = self._select_best_service()
        
        if service not in self.available_services:
            raise ValueError(f"Service '{service}' not available")
        
        # Generate output file if not provided
        if not output_file:
            output_file = os.path.join(tempfile.gettempdir(), f"tts_online_{uuid.uuid4().hex[:8]}.mp3")
        
        try:
            if service == "gtts":
                success = await self._synthesize_gtts(text, output_file, language)
            elif service == "azure":
                success = await self._synthesize_azure(text, output_file, voice, language, speed, pitch)
            elif service == "polly":
                success = await self._synthesize_polly(text, output_file, voice, language, speed)
            elif service == "watson":
                success = await self._synthesize_watson(text, output_file, voice, language)
            else:
                raise ValueError(f"Service not implemented: {service}")
            
            if success:
                file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
                result = {
                    "status": "success",
                    "text": text,
                    "service": service,
                    "output_file": output_file,
                    "file_size_bytes": file_size,
                    "language": language,
                    "voice": voice,
                    "speed": speed,
                    "pitch": pitch
                }
                
                logger.info(f"Online synthesis successful: {output_file} ({file_size} bytes)")
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                raise Exception("Online synthesis failed")
                
        except Exception as e:
            logger.error(f"Online synthesis error with {service}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": str(e),
                    "service": service,
                    "text": text
                })
            )]
    
    def _select_best_service(self) -> str:
        """Select the best available service"""
        if 'gtts' in self.available_services:
            return 'gtts'
        elif 'azure' in self.available_services:
            return 'azure'
        elif 'polly' in self.available_services:
            return 'polly'
        elif 'watson' in self.available_services:
            return 'watson'
        else:
            raise ValueError("No online TTS services available")
    
    async def _synthesize_gtts(self, text: str, output_file: str, language: str) -> bool:
        """Synthesize using Google TTS"""
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_file)
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"gTTS synthesis error: {e}")
            return False
    
    async def _synthesize_azure(self, text: str, output_file: str, voice: Optional[str], 
                               language: str, speed: str, pitch: str) -> bool:
        """Synthesize using Azure Cognitive Services"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            speech_config = speechsdk.SpeechConfig(
                subscription=os.getenv('AZURE_SPEECH_KEY'),
                region=os.getenv('AZURE_SPEECH_REGION')
            )
            
            # Set voice if specified
            if voice:
                speech_config.speech_synthesis_voice_name = voice
            else:
                # Default voices for common languages
                voice_map = {
                    'en': 'en-US-JennyNeural',
                    'es': 'es-ES-ElviraNeural',
                    'fr': 'fr-FR-DeniseNeural',
                    'de': 'de-DE-KatjaNeural',
                    'it': 'it-IT-ElsaNeural'
                }
                speech_config.speech_synthesis_voice_name = voice_map.get(language, 'en-US-JennyNeural')
            
            # Create SSML with speed and pitch
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
                <voice name="{speech_config.speech_synthesis_voice_name}">
                    <prosody rate="{speed}" pitch="{pitch}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Create synthesizer
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Synthesize
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True
            else:
                logger.error(f"Azure synthesis failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Azure synthesis error: {e}")
            return False
    
    async def _synthesize_polly(self, text: str, output_file: str, voice: Optional[str], 
                               language: str, speed: str) -> bool:
        """Synthesize using Amazon Polly"""
        try:
            polly_client = self.available_services['polly']['client']
            
            # Map speed to SSML rate
            speed_map = {
                'x-slow': '0.5',
                'slow': '0.75',
                'medium': '1.0',
                'fast': '1.25',
                'x-fast': '1.5'
            }
            
            # Create SSML
            ssml = f'<speak><prosody rate="{speed_map.get(speed, "1.0")}">{text}</prosody></speak>'
            
            # Default voices for languages
            if not voice:
                voice_map = {
                    'en': 'Joanna',
                    'es': 'Conchita',
                    'fr': 'Celine',
                    'de': 'Marlene',
                    'it': 'Carla'
                }
                voice = voice_map.get(language, 'Joanna')
            
            # Synthesize
            response = polly_client.synthesize_speech(
                Text=ssml,
                TextType='ssml',
                OutputFormat='mp3',
                VoiceId=voice
            )
            
            # Save audio
            with open(output_file, 'wb') as file:
                file.write(response['AudioStream'].read())
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"Polly synthesis error: {e}")
            return False
    
    async def _synthesize_watson(self, text: str, output_file: str, voice: Optional[str], language: str) -> bool:
        """Synthesize using IBM Watson"""
        try:
            watson_client = self.available_services['watson']['client']
            
            # Default voices
            if not voice:
                voice_map = {
                    'en': 'en-US_AllisonV3Voice',
                    'es': 'es-ES_EnriqueV3Voice',
                    'fr': 'fr-FR_ReneeV3Voice',
                    'de': 'de-DE_BirgitV3Voice',
                    'it': 'it-IT_FrancescaV3Voice'
                }
                voice = voice_map.get(language, 'en-US_AllisonV3Voice')
            
            # Synthesize
            response = watson_client.synthesize(
                text,
                voice=voice,
                accept='audio/mp3'
            ).get_result()
            
            # Save audio
            with open(output_file, 'wb') as audio_file:
                audio_file.write(response.content)
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logger.error(f"Watson synthesis error: {e}")
            return False
    
    async def _list_online_voices(self, arguments: dict) -> list[TextContent]:
        """List available voices for online services"""
        service = arguments.get("service", "gtts")
        language = arguments.get("language", "en")
        
        if service not in self.available_services:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Service '{service}' not available",
                    "available_services": list(self.available_services.keys())
                })
            )]
        
        voices_info = {"service": service, "language": language, "voices": []}
        
        try:
            if service == "gtts":
                # gTTS language codes
                voices_info["voices"] = [
                    {"id": "en", "name": "English", "gender": "neutral"},
                    {"id": "es", "name": "Spanish", "gender": "neutral"},
                    {"id": "fr", "name": "French", "gender": "neutral"},
                    {"id": "de", "name": "German", "gender": "neutral"},
                    {"id": "it", "name": "Italian", "gender": "neutral"},
                    {"id": "pt", "name": "Portuguese", "gender": "neutral"},
                    {"id": "ru", "name": "Russian", "gender": "neutral"},
                    {"id": "ja", "name": "Japanese", "gender": "neutral"},
                    {"id": "ko", "name": "Korean", "gender": "neutral"},
                    {"id": "zh", "name": "Chinese", "gender": "neutral"}
                ]
            
            elif service == "azure":
                # Sample Azure neural voices
                voices_info["voices"] = [
                    {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "language": "en-US"},
                    {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male", "language": "en-US"},
                    {"id": "en-GB-LibbyNeural", "name": "Libby", "gender": "female", "language": "en-GB"},
                    {"id": "es-ES-ElviraNeural", "name": "Elvira", "gender": "female", "language": "es-ES"},
                    {"id": "fr-FR-DeniseNeural", "name": "Denise", "gender": "female", "language": "fr-FR"},
                    {"id": "de-DE-KatjaNeural", "name": "Katja", "gender": "female", "language": "de-DE"}
                ]
            
            elif service == "polly":
                # Sample Polly voices
                voices_info["voices"] = [
                    {"id": "Joanna", "name": "Joanna", "gender": "female", "language": "en-US"},
                    {"id": "Matthew", "name": "Matthew", "gender": "male", "language": "en-US"},
                    {"id": "Amy", "name": "Amy", "gender": "female", "language": "en-GB"},
                    {"id": "Conchita", "name": "Conchita", "gender": "female", "language": "es-ES"},
                    {"id": "Celine", "name": "Celine", "gender": "female", "language": "fr-FR"},
                    {"id": "Marlene", "name": "Marlene", "gender": "female", "language": "de-DE"}
                ]
            
            voices_info["total_voices"] = len(voices_info["voices"])
            
        except Exception as e:
            voices_info["error"] = str(e)
        
        return [TextContent(type="text", text=json.dumps(voices_info, indent=2))]
    
    async def _get_service_limits(self, arguments: dict) -> list[TextContent]:
        """Get service limits and pricing information"""
        service = arguments.get("service")
        
        limits_info = {
            "gtts": {
                "free_tier": "Unlimited (rate limited)",
                "character_limit": "100 characters per request",
                "rate_limit": "Reasonable use policy",
                "pricing": "Free",
                "notes": "Google's free service with reasonable use limits"
            },
            "azure": {
                "free_tier": "5 million characters per month",
                "pricing_per_million": "$4.00 (Standard), $16.00 (Neural)",
                "character_limit": "No limit per request",
                "rate_limit": "20 transactions per second",
                "notes": "Requires Azure subscription after free tier"
            },
            "polly": {
                "free_tier": "5 million characters per month (first 12 months)",
                "pricing_per_million": "$4.00 (Standard), $16.00 (Neural)",
                "character_limit": "3000 characters per request",
                "rate_limit": "100 transactions per second",
                "notes": "AWS account required"
            },
            "watson": {
                "free_tier": "10,000 characters per month",
                "pricing_per_thousand": "$0.02",
                "character_limit": "5000 characters per request",
                "rate_limit": "10 transactions per second",
                "notes": "IBM Cloud account required"
            }
        }
        
        if service and service in limits_info:
            result = {"service": service, "limits": limits_info[service]}
        else:
            result = {"all_services": limits_info}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run_server(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-text-to-speech-online",
                    server_version="1.0.0",
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = OnlineTextToSpeechServer()
    await server.run_server()

if __name__ == "__main__":
    asyncio.run(main())
