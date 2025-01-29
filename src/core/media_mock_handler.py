from typing import Dict, Optional, Any, List
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MediaType(Enum):
    WEBRTC = "webrtc"
    CANVAS = "canvas" 
    WEBGL = "webgl"

class MediaMockHandler:
    """
    Handles WebRTC, Canvas and WebGL mocking using Playwright's capabilities
    """
    def __init__(self):
        self.mock_configs: Dict[str, Dict[str, Any]] = {
            MediaType.WEBRTC.value: {
                "enabled": True,
                "mock_video": True,
                "mock_audio": True,
                "video_file": None,
                "audio_file": None
            },
            MediaType.CANVAS.value: {
                "enabled": True,
                "noise_value": 0.1,  # Add slight noise to prevent fingerprinting
                "mock_readback": True
            },
            MediaType.WEBGL.value: {
                "enabled": True,
                "vendor": "Mock GL Vendor",
                "renderer": "Mock GL Renderer",
                "noise_value": 0.05
            }
        }

    async def setup_mocks(self, context) -> None:
        """Setup all media mocks for a browser context"""
        if not context:
            raise ValueError("Browser context is not initialized")

        try:
            # Setup WebRTC mocking
            await self._setup_webrtc_mock(context)
            
            # Setup Canvas mocking
            await self._setup_canvas_mock(context)
            
            # Setup WebGL mocking
            await self._setup_webgl_mock(context)
            
            logger.debug("Media mocking setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup media mocks: {str(e)}")
            raise

    async def _setup_webrtc_mock(self, context) -> None:
        """Setup WebRTC mocking"""
        if not self.mock_configs[MediaType.WEBRTC.value]["enabled"]:
            return

        # Inject WebRTC mocking script
        await context.add_init_script("""
            window.navigator.mediaDevices.getUserMedia = async (constraints) => {
                const mockStream = new MediaStream();
                if (constraints.video) {
                    mockStream.addTrack(createMockVideoTrack());
                }
                if (constraints.audio) {
                    mockStream.addTrack(createMockAudioTrack());
                }
                return mockStream;
            };

            function createMockVideoTrack() {
                const canvas = Object.assign(document.createElement('canvas'), {
                    width: 640,
                    height: 480
                });
                const ctx = canvas.getContext('2d');
                const stream = canvas.captureStream(30);  // 30 FPS
                setInterval(() => {
                    // Draw something to simulate video
                    ctx.fillStyle = '#' + Math.floor(Math.random()*16777215).toString(16);
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                }, 1000 / 30);
                return stream.getVideoTracks()[0];
            }

            function createMockAudioTrack() {
                const ctx = new AudioContext();
                const oscillator = ctx.createOscillator();
                const dst = oscillator.connect(ctx.createMediaStreamDestination());
                oscillator.start();
                return dst.stream.getAudioTracks()[0];
            }
        """)

    async def _setup_canvas_mock(self, context) -> None:
        """Setup Canvas mocking"""
        if not self.mock_configs[MediaType.CANVAS.value]["enabled"]:
            return

        noise_value = self.mock_configs[MediaType.CANVAS.value]["noise_value"]
        
        await context.add_init_script(f"""
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function() {{
                const context = originalGetContext.apply(this, arguments);
                if (context && (arguments[0] === '2d' || arguments[0] === 'bitmaprenderer')) {{
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function() {{
                        const imageData = originalGetImageData.apply(this, arguments);
                        // Add noise to prevent fingerprinting
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] += Math.floor(Math.random() * {noise_value} * 255);
                            imageData.data[i + 1] += Math.floor(Math.random() * {noise_value} * 255);
                            imageData.data[i + 2] += Math.floor(Math.random() * {noise_value} * 255);
                        }}
                        return imageData;
                    }};
                }}
                return context;
            }};
        """)

    async def _setup_webgl_mock(self, context) -> None:
        """Setup WebGL mocking"""
        if not self.mock_configs[MediaType.WEBGL.value]["enabled"]:
            return

        config = self.mock_configs[MediaType.WEBGL.value]
        
        await context.add_init_script(f"""
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function() {{
                const context = originalGetContext.apply(this, arguments);
                if (context && (arguments[0] === 'webgl' || arguments[0] === 'webgl2')) {{
                    const getParameter = context.getParameter.bind(context);
                    context.getParameter = function(parameter) {{
                        // Mock WebGL parameters
                        if (parameter === context.VENDOR) {{
                            return "{config['vendor']}";
                        }}
                        if (parameter === context.RENDERER) {{
                            return "{config['renderer']}";
                        }}
                        return getParameter(parameter);
                    }};
                }}
                return context;
            }};
        """)

    def configure_mock(self, media_type: str, config: Dict[str, Any]) -> None:
        """Configure specific media mock settings"""
        if media_type not in self.mock_configs:
            raise ValueError(f"Invalid media type: {media_type}")
            
        self.mock_configs[media_type].update(config)
        logger.debug(f"Updated {media_type} mock configuration: {config}")

    def get_mock_config(self, media_type: str) -> Dict[str, Any]:
        """Get current mock configuration"""
        return self.mock_configs.get(media_type, {}) 