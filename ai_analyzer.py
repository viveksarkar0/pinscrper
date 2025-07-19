import google.generativeai as genai
import json
import requests
from PIL import Image
import io
from typing import Dict, List, Optional
import logging
from fashion_taxonomy import *
import os
from dotenv import load_dotenv

load_dotenv()

class FashionAIAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def download_image(self, image_url: str) -> Optional[Image.Image]:
        """Download image from URL and return PIL Image"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            return image
        except Exception as e:
            self.logger.error(f"Error downloading image from {image_url}: {e}")
            return None
    
    def analyze_fashion_image(self, image: Image.Image, pin_title: str = "", pin_description: str = "") -> Dict:
        """Analyze fashion image using Gemini AI"""
        try:
            # Create comprehensive prompt for fashion analysis
            prompt = self.create_fashion_analysis_prompt(pin_title, pin_description)
            
            # Generate analysis using Gemini
            response = self.model.generate_content([prompt, image])
            
            # Parse the response
            analysis_result = self.parse_ai_response(response.text)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing fashion image: {e}")
            return {
                'error': str(e),
                'fashion_items': [],
                'style_analysis': {},
                'confidence_score': 0.0
            }
    
    def create_fashion_analysis_prompt(self, title: str = "", description: str = "") -> str:
        """Create comprehensive prompt for fashion analysis matching user's expected format"""
        context = ""
        if title:
            context += f"Pin Title: {title}\n"
        if description:
            context += f"Pin Description: {description}\n"
        
        prompt = f"""
        {context}
        
        🚀 Advanced Fashion Analysis System
        
        Analyze this fashion image and provide a comprehensive fashion analysis report. 
        Return your response as a JSON object with the following detailed structure:

        {{
            "detected_fashion_items": [
                {{
                    "item_number": 1,
                    "category": "Dress/Top/Pants/Shoes/Accessory",
                    "type": "specific_type_like_mini_dress_or_blazer",
                    "colors": ["primary_color", "secondary_color"],
                    "material": "fabric_type_like_leather_cotton_silk",
                    "style": "style_description_like_formal_casual_edgy",
                    "details": {{
                        "length": "mini/midi/maxi/ankle/etc",
                        "fit": "fitted/loose/oversized/etc",
                        "special_features": "unique_design_elements"
                    }}
                }}
            ],
            "comprehensive_style_analysis": {{
                "overall_aesthetic": "detailed_description_of_the_complete_look_and_vibe",
                "style_category": "primary_style_like_Modern_Glamour_Boho_Chic_Street_Style",
                "style_influences": ["influence1", "influence2"],
                "occasion_suitability": ["evening_events", "casual_outings", "formal_occasions"]
            }},
            "color_analysis": {{
                "dominant_colors": ["main_colors_in_outfit"],
                "color_palette": "description_of_color_scheme",
                "color_harmony": "monochromatic/complementary/analogous/etc",
                "seasonal_association": "Spring/Summer/Autumn/Winter",
                "color_psychology": "what_the_colors_convey_about_personality"
            }},
            "silhouette_analysis": {{
                "overall_silhouette": "body_shape_created_by_outfit",
                "proportions": "how_proportions_work_together",
                "fit_philosophy": "fitted/relaxed/structured/etc",
                "body_emphasis": "what_parts_are_highlighted"
            }},
            "fabric_and_texture_analysis": {{
                "primary_fabrics": ["main_materials_used"],
                "texture_mix": "description_of_texture_combinations",
                "quality_indicators": "signs_of_luxury_or_quality",
                "seasonal_appropriateness": "how_fabrics_suit_seasons"
            }},
            "styling_techniques": {{
                "key_styling_choices": ["notable_styling_decisions"],
                "accessories_impact": "how_accessories_complete_look",
                "balance_and_proportion": "styling_balance_achieved"
            }},
            "trend_analysis": {{
                "current_trends": ["trending_elements_in_outfit"],
                "timeless_elements": ["classic_pieces_that_endure"],
                "trend_longevity": "how_long_this_style_will_remain_relevant",
                "future_outlook": "prediction_for_style_evolution"
            }},
            "occasion_analysis": {{
                "perfect_for": ["ideal_occasions_for_this_outfit"],
                "versatility": "how_adaptable_the_look_is",
                "dress_code_suitability": "formal/semi-formal/casual/cocktail/etc"
            }},
            "brand_and_luxury_indicators": {{
                "similar_brands": ["brands_with_similar_aesthetic"],
                "estimated_price_point": "high-end/mid-range/accessible",
                "luxury_indicators": ["signs_of_premium_quality"]
            }},
            "personal_style_insights": {{
                "personality_traits": ["confident", "bold", "creative", "etc"],
                "style_persona": "overall_fashion_personality_conveyed",
                "fashion_confidence_level": "high/medium/experimental"
            }},
            "confidence_score": 0.85
        }}

        IMPORTANT: Provide detailed, specific analysis for each section. Be descriptive and insightful.
        Focus on:
        1. Detailed identification of all visible fashion items
        2. Comprehensive color and fabric analysis
        3. Style categorization and aesthetic description
        4. Trend awareness and fashion insights
        5. Occasion and versatility assessment
        6. Quality and brand positioning
        
        Make the analysis rich, detailed, and fashion-forward like a professional stylist would provide.
        """
        
        return prompt
    
    def parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response and extract structured data"""
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis_data = json.loads(json_str)
                return analysis_data
            else:
                # If no JSON found, create structured response from text
                return self.create_fallback_analysis(response_text)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return self.create_fallback_analysis(response_text)
    
    def create_fallback_analysis(self, response_text: str) -> Dict:
        """Create fallback analysis structure when JSON parsing fails"""
        return {
            'detected_fashion_items': [
                {
                    'item_number': 1,
                    'category': 'Unknown',
                    'type': 'Fashion Item',
                    'colors': [],
                    'material': 'Unknown',
                    'style': 'General',
                    'details': {
                        'length': 'Unknown',
                        'fit': 'Unknown',
                        'special_features': 'Unable to analyze'
                    }
                }
            ],
            'comprehensive_style_analysis': {
                'overall_aesthetic': response_text[:200] + "..." if len(response_text) > 200 else response_text,
                'style_category': 'General Fashion',
                'style_influences': [],
                'occasion_suitability': ['General wear']
            },
            'color_analysis': {
                'dominant_colors': [],
                'color_palette': 'Mixed',
                'color_harmony': 'Unknown',
                'seasonal_association': 'All Seasons',
                'color_psychology': 'Unable to determine'
            },
            'silhouette_analysis': {
                'overall_silhouette': 'Unknown',
                'proportions': 'Standard',
                'fit_philosophy': 'Contemporary',
                'body_emphasis': 'Unknown'
            },
            'fabric_and_texture_analysis': {
                'primary_fabrics': [],
                'texture_mix': 'Mixed textures',
                'quality_indicators': 'Standard quality',
                'seasonal_appropriateness': 'All seasons'
            },
            'styling_techniques': {
                'key_styling_choices': [],
                'accessories_impact': 'Unable to analyze',
                'balance_and_proportion': 'Standard'
            },
            'trend_analysis': {
                'current_trends': [],
                'timeless_elements': [],
                'trend_longevity': 'Moderate',
                'future_outlook': 'Stable'
            },
            'occasion_analysis': {
                'perfect_for': ['General occasions'],
                'versatility': 'Moderate',
                'dress_code_suitability': 'Casual'
            },
            'brand_and_luxury_indicators': {
                'similar_brands': [],
                'estimated_price_point': 'mid-range',
                'luxury_indicators': []
            },
            'personal_style_insights': {
                'personality_traits': ['General'],
                'style_persona': 'Everyday fashion',
                'fashion_confidence_level': 'medium'
            },
            'confidence_score': 0.5
        }
    
    def analyze_pin(self, pin_data: Dict) -> Dict:
        """Analyze a single pin's image and return fashion analysis"""
        try:
            image_url = pin_data.get('image_url')
            if not image_url:
                return {'error': 'No image URL provided'}
            
            # Download the image
            image = self.download_image(image_url)
            if not image:
                return {'error': 'Failed to download image'}
            
            # Analyze the image
            analysis = self.analyze_fashion_image(
                image, 
                pin_data.get('title', ''), 
                pin_data.get('description', '')
            )
            
            # Add metadata
            analysis['pin_id'] = pin_data.get('pin_id')
            analysis['image_url'] = image_url
            analysis['analyzed_at'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing pin {pin_data.get('pin_id', 'unknown')}: {e}")
            return {
                'error': str(e),
                'pin_id': pin_data.get('pin_id'),
                'confidence_score': 0.0
            }
    
    def batch_analyze_pins(self, pins_data: List[Dict], batch_size: int = 10) -> List[Dict]:
        """Analyze multiple pins in batches"""
        results = []
        total_pins = len(pins_data)
        
        self.logger.info(f"Starting batch analysis of {total_pins} pins")
        
        for i in range(0, total_pins, batch_size):
            batch = pins_data[i:i + batch_size]
            batch_results = []
            
            for j, pin_data in enumerate(batch):
                try:
                    self.logger.info(f"Analyzing pin {i + j + 1}/{total_pins}")
                    analysis = self.analyze_pin(pin_data)
                    batch_results.append(analysis)
                    
                    # Add small delay to avoid rate limiting
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error in batch analysis: {e}")
                    batch_results.append({
                        'error': str(e),
                        'pin_id': pin_data.get('pin_id'),
                        'confidence_score': 0.0
                    })
            
            results.extend(batch_results)
            self.logger.info(f"Completed batch {i//batch_size + 1}/{(total_pins + batch_size - 1)//batch_size}")
        
        self.logger.info(f"Completed analysis of {len(results)} pins")
        return results
