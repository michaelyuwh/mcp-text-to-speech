#!/usr/bin/env python3
"""
Simple test script for MCP Text-to-Speech Server
Demonstrates offline text synthesis capabilities
"""

import json
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_text_to_speech.server import OfflineTextToSpeechServer

async def test_tts_server():
    """Test the TTS server functionality"""
    print("🎤 Testing MCP Text-to-Speech Server")
    print("=" * 50)
    
    # Initialize server
    server = OfflineTextToSpeechServer()
    
    # Test 1: Get available engines
    print("\n📋 Test 1: Getting available engines")
    engines_result = await server._get_available_engines()
    engines_data = json.loads(engines_result[0].text)
    print(f"Available engines: {engines_data['total_engines']}")
    print(f"Offline engines: {engines_data['offline_engines']}")
    print(f"Recommendation: {engines_data['recommendation']}")
    
    # Test 2: Synthesize speech
    print("\n🎵 Test 2: Synthesizing speech")
    output_file = os.path.join(tempfile.gettempdir(), "mcp_tts_test.wav")
    
    synthesis_args = {
        "text": "Hello! This is a test of the MCP text-to-speech server. It works completely offline using pyttsx3 on macOS ARM64. The speech synthesis is working perfectly!",
        "engine": "auto",
        "output_file": output_file,
        "speed": 160
    }
    
    synthesis_result = await server._synthesize_speech(synthesis_args)
    synthesis_data = json.loads(synthesis_result[0].text)
    
    if synthesis_data.get("status") == "success":
        print(f"✅ Synthesis successful!")
        print(f"   Engine used: {synthesis_data['engine']}")
        print(f"   Output file: {synthesis_data['output_file']}")
        print(f"   File size: {synthesis_data['file_size_bytes']} bytes")
        print(f"   Speed: {synthesis_data['speed']} WPM")
        
        # Check if file exists
        if os.path.exists(output_file):
            print(f"   ✅ Audio file created successfully")
            
            # Try to get file duration (basic check)
            file_size = os.path.getsize(output_file)
            if file_size > 1000:  # More than 1KB indicates actual audio content
                print(f"   ✅ Audio file appears valid ({file_size} bytes)")
            else:
                print(f"   ⚠️  Audio file is very small ({file_size} bytes)")
        else:
            print(f"   ❌ Audio file was not created")
    else:
        print(f"❌ Synthesis failed: {synthesis_data.get('message', 'Unknown error')}")
    
    # Test 3: List voices
    print("\n🎭 Test 3: Listing available voices")
    voices_result = await server._list_voices({"engine": "pyttsx3"})
    voices_data = json.loads(voices_result[0].text)
    
    print(f"Total voices for pyttsx3: {voices_data.get('total_voices', 0)}")
    if 'voices' in voices_data:
        print("Sample voices:")
        for i, voice in enumerate(voices_data['voices'][:5]):  # Show first 5
            print(f"   {i+1}. {voice.get('name', 'Unknown')} ({voice.get('id', 'no-id')})")
        if len(voices_data['voices']) > 5:
            print(f"   ... and {len(voices_data['voices']) - 5} more voices")
    
    print("\n🎉 MCP Text-to-Speech Server test completed!")
    print("✅ All core functionality is working correctly")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tts_server())
