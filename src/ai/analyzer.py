import openai
import logging
from typing import Dict, Optional, List
import yaml
from PIL import Image
import pytesseract
import requests
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentAnalyzer:
    def __init__(self, api_key: str, config_path: str = "config/config.yaml"):
        self.client = openai.OpenAI(api_key=api_key)
        self.config = self._load_config(config_path)
        self.confidence_threshold = self.config['ai']['confidence_threshold']
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text content using GPT-4."""
        try:
            prompt = self.config['ai']['analysis_prompts']['text'].format(content=text)
            
            response = self.client.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a crypto trading analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['ai']['openai']['temperature'],
                max_tokens=self.config['ai']['openai']['max_tokens']
            )
            
            analysis = response.choices[0].message.content  # type: ignore
            
            # Extract structured data from the analysis
            return self._parse_analysis(analysis)  # type: ignore
            
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {}
    
    def analyze_image(self, image_url: str) -> Dict:
        """Analyze trading chart images."""
        try:
            # Download and process image
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Extract text from image using OCR
            ocr_text = pytesseract.image_to_string(image)
            
            # Analyze the extracted text
            prompt = self.config['ai']['analysis_prompts']['image'].format(content=ocr_text)
            
            response = self.client.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a crypto trading chart analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['ai']['openai']['temperature'],
                max_tokens=self.config['ai']['openai']['max_tokens']
            )
            
            analysis = response.choices[0].message.content
            
            return self._parse_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {}
    
    def analyze_video(self, video_url: str) -> Dict:
        """Analyze video content using OpenAI's vision capabilities."""
        try:
            # For video analysis, we'll extract frames and analyze them
            # This is a simplified implementation - in production you might want to use
            # a video processing library to extract key frames
            
            # For now, we'll analyze the video thumbnail/preview image
            # You can enhance this by extracting multiple frames from the video
            
            # Download video thumbnail (if available)
            # Most video platforms provide thumbnail URLs
            thumbnail_url = video_url.replace('.mp4', '_thumb.jpg')  # Example
            
            try:
                # Try to get thumbnail
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    # Analyze the thumbnail image
                    return self.analyze_image(thumbnail_url)
            except:
                pass
            
            # If thumbnail analysis fails, try to analyze the video URL directly
            # This works for some video platforms that support direct image analysis
            try:
                # Use OpenAI's vision model to analyze the video
                prompt = self.config['ai']['analysis_prompts']['video'].format(content="video content")
                
                response = self.client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": video_url,
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=self.config['ai']['openai']['max_tokens']
                )
                
                analysis = response.choices[0].message.content
                return self._parse_analysis(analysis)
                
            except Exception as e:
                logger.warning(f"Video analysis failed, falling back to text analysis: {str(e)}")
                # Fallback: return empty dict and let text analysis handle it
                return {}
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return {}
    
    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse AI analysis into structured data."""
        try:
            # Extract key information using GPT-4
            prompt = f"""
            Extract the following information from this trading analysis:
            - Trading pair/symbol
            - Direction (LONG/SHORT)
            - Entry price
            - Stop loss
            - Take profit levels
            - Timeframe
            - Confidence level (0-1)
            - Reasoning
            
            Analysis: {analysis}
            
            Return the information in a structured format.
            """
            
            response = self.client.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a data extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=500
            )
            
            extracted_data = response.choices[0].message.content
            
            # Convert the extracted data into a structured format
            # This is a simplified version - you might want to make this more robust
            return {
                'symbol': self._extract_value(extracted_data, 'symbol'),
                'direction': self._extract_value(extracted_data, 'direction'),
                'entry_price': float(self._extract_value(extracted_data, 'entry price')),
                'stop_loss': float(self._extract_value(extracted_data, 'stop loss')),
                'take_profit': [float(x) for x in self._extract_value(extracted_data, 'take profit').split(',')],
                'timeframe': self._extract_value(extracted_data, 'timeframe'),
                'confidence': float(self._extract_value(extracted_data, 'confidence')),
                'reasoning': self._extract_value(extracted_data, 'reasoning')
            }
            
        except Exception as e:
            logger.error(f"Error parsing analysis: {str(e)}")
            return {}
    
    def _extract_value(self, text: str, key: str) -> str:
        """Helper method to extract values from text."""
        try:
            # Simple extraction - you might want to make this more robust
            lines = text.split('\n')
            for line in lines:
                if key.lower() in line.lower():
                    return line.split(':')[1].strip()
            return ""
        except Exception:
            return "" 