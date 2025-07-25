#!/usr/bin/env python3
"""
AI Fashion Analyzer Module
Enhanced version of your existing fashion analyzer with production features
"""

import google.generativeai as genai
import json
import enum
import typing
from PIL import Image
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# =============================================================================
# FASHION TAXONOMY DEFINITIONS (From your existing code)
# =============================================================================

class ApparelCategory(enum.Enum):
    DRESS = "Dress"
    TOP = "Top"
    KNIT_TOP = "Knit or Sweater Top"
    SHIRT = "Shirt"
    PANTS = "Pants"
    SHORTS = "Shorts"
    SKIRT = "Skirt"
    SHOES = "Shoes"
    OUTERWEAR = "Outerwear"
    UNDERGARMENTS = "Undergarments"
    BAG = "Bag"
    ACCESSORY = "Accessory"

class Waist(enum.Enum):
    RIB_CAGE = "Rib cage"
    HIGH_WAISTED = "High Waisted"
    NATURAL_WAIST = "Natural Waist"
    MIDRISE = "Midrise"
    LOWRISE = "Lowrise"
    HIP_HUGGER = "Hip Hugger"

class PantsType(enum.Enum):
    JEANS = "Jeans"
    CHINOS = "Chinos"
    JOGGERS = "Joggers"
    FORMAL = "Formal"
    CARGO = "Cargo"

class PantsLength(enum.Enum):
    FULL_LENGTH = "Full Length"
    ANKLE = "Ankle"
    CROPPED = "Cropped"
    SHORTS = "Shorts"

class ShirtStyle(enum.Enum):
    BUTTON_DOWN = "Button Down"
    POLO = "Polo"
    TEE = "T-shirt"
    LONG_SLEEVE = "Long Sleeve"
    SHORT_SLEEVE = "Short Sleeve"

class ShoeType(enum.Enum):
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    FORMAL_SHOES = "Formal Shoes"
    SLIPPERS = "Slippers"

class WatchType(enum.Enum):
    ANALOG = "Analog"
    DIGITAL = "Digital"
    SMARTWATCH = "Smartwatch"

class FabricDetails(typing.TypedDict):
    material: str
    texture: str

class ClothingItem(typing.TypedDict):
    category: ApparelCategory
    colors: list[str]
    fabric: str
    fabric_details: list[FabricDetails]
    specific_type: str
    additional_attributes: dict

class FashionCategory(enum.Enum):
    CLOTHING = "Clothing"
    FOOTWEAR = "Footwear"
    ACCESSORY = "Accessory"
    BAG = "Bag"

class FootwearType(enum.Enum):
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    FORMAL_SHOES = "Formal Shoes"
    SLIPPERS = "Slippers"

class FashionItem(typing.TypedDict):
    category: FashionCategory
    type: str
    color: str
    material: str
    style: str
    brand: str

# =============================================================================
# AI FASHION ANALYZER CLASS
# =============================================================================

class AIFashionAnalyzer:
    """Production-level AI Fashion Analyzer with enhanced capabilities"""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-002'):
        """Initialize the AI Fashion Analyzer"""
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini AI
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        self.logger.info(f"AI Fashion Analyzer initialized with model: {model_name}")
    
    # =============================================================================
    # PROMPTS (Enhanced versions of your existing prompts)
    # =============================================================================
    
    @property
    def identifier_prompt(self) -> str:
        """Enhanced fashion item identification prompt"""
        return '''
        Identify and classify all fashion-related items in the image using the defined taxonomy.
        For each detected fashion item, return a structured JSON following these rules:

        - "category": Choose from ["Clothing", "Footwear", "Accessory", "Bag"].
        - "type": The specific item type (e.g., "T-shirt", "Jeans", "Sneakers", "Watch").
        - "color": List of detected colors (be specific, e.g., "navy blue", "forest green").
        - "material": The primary material (e.g., "Denim", "Leather", "Cotton", "Metal").
        - "style": The fashion style (e.g., "Casual", "Formal", "Sporty", "Bohemian").
        - "brand": The visible brand name (if identifiable) or "Unknown".
        - "confidence": Confidence score from 0.0 to 1.0 for this identification.

        If the item belongs to "Clothing", also include:
        - "fabric_details": List of material and texture information.
        - "specific_type": More specific clothing type (e.g., "Maxi Dress", "Crew Neck T-shirt", "Skinny Jeans").
        - "additional_attributes": Category-specific details such as:
          - For Pants: "pants_type", "length", "waist", "fit" (slim, regular, loose)
          - For Shirts: "shirt_style", "neckline", "sleeve_type", "collar_type"
          - For Dresses: "dress_length", "neckline", "sleeve_type", "silhouette"
          - For Shoes: "shoe_type", "heel_height", "closure_type", "toe_shape"
          - For Bags: "bag_type", "closure_type", "size", "handle_type"
          - For Accessories: "accessory_type", "material", "size", "style"

        Additional analysis:
        - "season_appropriateness": Which seasons this item is suitable for
        - "occasion_suitability": Occasions where this item would be appropriate
        - "price_range_estimate": Estimated price range (budget/mid-range/luxury)
        - "trend_status": Current trend status (trending/classic/outdated)

        Return JSON format:
        {
            "fashion_items": [
                {
                    "category": "...",
                    "type": "...",
                    "color": ["..."],
                    "material": "...",
                    "style": "...",
                    "brand": "...",
                    "confidence": 0.0,
                    "fabric_details": [{"material": "...", "texture": "..."}],
                    "specific_type": "...",
                    "additional_attributes": {...},
                    "season_appropriateness": ["..."],
                    "occasion_suitability": ["..."],
                    "price_range_estimate": "...",
                    "trend_status": "..."
                }
            ],
            "overall_outfit_analysis": {
                "style_coherence": "...",
                "color_harmony": "...",
                "occasion_appropriateness": "...",
                "overall_rating": 0.0
            }
        }

        If no relevant fashion items are detected, return {"fashion_items": []}.
        '''
    
    @property
    def advanced_style_prompt(self) -> str:
        """Enhanced advanced style analysis prompt"""
        return '''
        Based on the fashion items detected in the image, provide a comprehensive, professional fashion analysis 
        similar to how fashion experts analyze outfits for magazines and style blogs. 
        
        Return a JSON response with the following structure:

        {
          "style_analysis": {
            "overall_aesthetic": "Detailed description of the overall style aesthetic",
            "style_category": "Specific style category (e.g., 'Minimalist Chic', 'Street Style', 'Business Casual')",
            "style_confidence_score": 0.0,
            
            "influencer_matches": [
              {
                "name": "Fashion influencer/celebrity name",
                "instagram": "@handle",
                "similarity_reason": "Why this person's style matches",
                "style_notes": "Specific style elements they share",
                "confidence": 0.0
              }
            ],
            
            "color_analysis": {
              "primary_palette": ["main colors"],
              "secondary_palette": ["accent colors"],
              "color_harmony_type": "monochromatic/analogous/complementary/triadic",
              "color_temperature": "warm/cool/neutral",
              "seasonal_color_analysis": "spring/summer/autumn/winter",
              "color_psychology": "What the color choices convey",
              "color_coordination_score": 0.0
            },
            
            "silhouette_analysis": {
              "overall_shape": "Description of the outfit's silhouette",
              "proportions": "Analysis of proportions and balance",
              "fit_quality": "oversized/fitted/tailored/loose",
              "body_type_suitability": ["body types this outfit flatters"],
              "silhouette_score": 0.0
            },
            
            "fabric_texture_analysis": {
              "texture_variety": "smooth/textured/mixed",
              "fabric_quality_indicators": ["signs of quality or lack thereof"],
              "seasonal_appropriateness": "how fabrics suit the season",
              "comfort_level": "estimated comfort level",
              "care_requirements": "estimated maintenance needs"
            },
            
            "styling_techniques": [
              "Specific styling techniques used (layering, color blocking, etc.)"
            ],
            
            "fashion_details": [
              "Subtle fashion details and styling choices"
            ],
            
            "occasion_analysis": {
              "primary_occasions": ["Best occasions for this outfit"],
              "versatility_score": 0.0,
              "dress_code_compliance": {
                "casual": true/false,
                "business_casual": true/false,
                "formal": true/false,
                "black_tie": true/false
              },
              "time_of_day_suitability": ["morning", "afternoon", "evening"]
            },
            
            "trend_analysis": {
              "current_trends_represented": ["trending elements"],
              "timeless_elements": ["classic elements"],
              "trend_forecast_alignment": "how this fits future trends",
              "trend_adoption_level": "early_adopter/mainstream/late_adopter",
              "trend_longevity_prediction": "short-term/seasonal/long-term"
            },
            
            "brand_market_analysis": {
              "similar_aesthetic_brands": ["brands with similar style"],
              "estimated_price_point": "budget/affordable/mid-range/premium/luxury",
              "target_demographic": "age range and lifestyle",
              "luxury_indicators": ["elements suggesting quality/luxury"],
              "value_proposition": "cost vs style value assessment"
            },
            
            "personal_style_psychology": {
              "personality_indicators": ["traits this style suggests"],
              "lifestyle_alignment": ["lifestyle this outfit indicates"],
              "confidence_projection": "how confident this style appears",
              "social_signaling": "what this outfit communicates socially",
              "self_expression_level": "conservative/moderate/bold"
            },
            
            "improvement_recommendations": [
              "Specific actionable styling improvements"
            ],
            
            "sustainability_assessment": {
              "sustainable_elements": ["eco-friendly aspects if visible"],
              "longevity_potential": "how long this style will remain relevant",
              "investment_piece_identification": ["items worth investing in"],
              "cost_per_wear_optimization": "suggestions for maximizing value"
            },
            
            "cultural_context": {
              "cultural_influences": ["visible cultural style influences"],
              "geographic_style_indicators": ["regional style elements"],
              "generational_appeal": ["age groups this would appeal to"]
            },
            
            "technical_fashion_analysis": {
              "construction_quality_indicators": ["visible quality markers"],
              "fit_technical_assessment": "professional fit analysis",
              "fabric_drape_analysis": "how fabrics fall and move",
              "proportion_mathematics": "golden ratio and proportion analysis"
            }
          },
          
          "actionable_insights": {
            "immediate_improvements": ["quick fixes"],
            "shopping_recommendations": ["what to buy next"],
            "styling_alternatives": ["different ways to wear these items"],
            "seasonal_adaptations": ["how to adapt for different seasons"]
          },
          
          "overall_scores": {
            "style_execution": 0.0,
            "trend_relevance": 0.0,
            "versatility": 0.0,
            "quality_perception": 0.0,
            "overall_fashion_score": 0.0
          }
        }

        Be extremely detailed and provide specific, actionable insights. Consider current fashion trends, 
        color theory, body proportion principles, fabric science, brand positioning, and cultural context.
        All scores should be between 0.0 and 10.0.
        '''
    
    def analyze_fashion_items(self, image_path: str) -> Optional[Dict]:
        """Analyze fashion items in an image"""
        try:
            # Load image
            image = Image.open(image_path)
            self.logger.info(f"Analyzing fashion items in: {Path(image_path).name}")
            
            # Generate content with fashion identification prompt
            response = self.model.generate_content(
                [image, self.identifier_prompt], 
                generation_config=self.generation_config
            )
            
            # Parse response
            if hasattr(response, '_result') and hasattr(response._result, 'candidates'):
                candidates = response._result.candidates
                if candidates:
                    content_text = candidates[0].content.parts[0].text
                    analysis_data = json.loads(content_text)
                    
                    self.logger.info(f"Fashion items analysis completed for: {Path(image_path).name}")
                    return analysis_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fashion items analysis failed for {image_path}: {e}")
            return None
    
    def analyze_advanced_style(self, image_path: str, fashion_items: Optional[Dict] = None) -> Optional[Dict]:
        """Perform advanced style analysis"""
        try:
            # Load image
            image = Image.open(image_path)
            self.logger.info(f"Performing advanced style analysis for: {Path(image_path).name}")
            
            # Create prompt with detected items context if available
            prompt = self.advanced_style_prompt
            if fashion_items:
                context = f"Based on these detected fashion items:\n{json.dumps(fashion_items, indent=2)}\n\n{prompt}"
            else:
                context = prompt
            
            # Generate content
            response = self.model.generate_content(
                [image, context], 
                generation_config=self.generation_config
            )
            
            # Parse response
            if hasattr(response, '_result') and hasattr(response._result, 'candidates'):
                candidates = response._result.candidates
                if candidates:
                    content_text = candidates[0].content.parts[0].text
                    style_analysis = json.loads(content_text)
                    
                    self.logger.info(f"Advanced style analysis completed for: {Path(image_path).name}")
                    return style_analysis
            
            return None
            
        except Exception as e:
            self.logger.error(f"Advanced style analysis failed for {image_path}: {e}")
            return None
    
    def comprehensive_analysis(self, image_path: str) -> Dict:
        """Perform comprehensive fashion analysis (items + advanced style)"""
        self.logger.info(f"Starting comprehensive analysis for: {Path(image_path).name}")
        
        # Step 1: Analyze fashion items
        fashion_items = self.analyze_fashion_items(image_path)
        
        # Step 2: Perform advanced style analysis
        style_analysis = self.analyze_advanced_style(image_path, fashion_items)
        
        # Combine results
        comprehensive_result = {
            "image_path": str(image_path),
            "analysis_timestamp": datetime.now().isoformat(),
            "fashion_items_analysis": fashion_items or {},
            "advanced_style_analysis": style_analysis or {},
            "analysis_success": {
                "fashion_items": fashion_items is not None,
                "style_analysis": style_analysis is not None
            }
        }
        
        self.logger.info(f"Comprehensive analysis completed for: {Path(image_path).name}")
        return comprehensive_result
    
    def batch_analyze(self, image_paths: List[str], output_dir: str = "analysis_results") -> List[Dict]:
        """Analyze multiple images in batch"""
        self.logger.info(f"Starting batch analysis of {len(image_paths)} images")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            self.logger.info(f"Processing image {i}/{len(image_paths)}: {Path(image_path).name}")
            
            try:
                # Perform comprehensive analysis
                result = self.comprehensive_analysis(image_path)
                results.append(result)
                
                # Save individual result
                result_filename = f"analysis_{Path(image_path).stem}.json"
                result_path = output_path / result_filename
                
                with open(result_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                self.logger.info(f"Saved analysis result to: {result_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {image_path}: {e}")
                # Add error result
                error_result = {
                    "image_path": str(image_path),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "analysis_success": {
                        "fashion_items": False,
                        "style_analysis": False
                    }
                }
                results.append(error_result)
        
        # Save batch results
        batch_result_path = output_path / "batch_analysis_results.json"
        batch_summary = {
            "total_images": len(image_paths),
            "successful_analyses": len([r for r in results if r.get("analysis_success", {}).get("fashion_items", False)]),
            "batch_timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        with open(batch_result_path, 'w') as f:
            json.dump(batch_summary, f, indent=2)
        
        self.logger.info(f"Batch analysis completed. Results saved to: {batch_result_path}")
        return results
    
    def extract_training_labels(self, analysis_result: Dict) -> Dict:
        """Extract labels suitable for ML training from analysis result"""
        labels = {
            "categories": [],
            "types": [],
            "colors": [],
            "materials": [],
            "styles": [],
            "brands": [],
            "occasions": [],
            "seasons": [],
            "price_ranges": [],
            "trend_status": [],
            "tags": []
        }
        
        # Extract from fashion items analysis
        fashion_items = analysis_result.get("fashion_items_analysis", {}).get("fashion_items", [])
        
        for item in fashion_items:
            # Basic attributes
            if "category" in item:
                labels["categories"].append(item["category"].lower())
            if "type" in item:
                labels["types"].append(item["type"].lower().replace(" ", "_"))
            if "color" in item:
                colors = item["color"] if isinstance(item["color"], list) else [item["color"]]
                labels["colors"].extend([c.lower().replace(" ", "_") for c in colors])
            if "material" in item:
                labels["materials"].append(item["material"].lower().replace(" ", "_"))
            if "style" in item:
                labels["styles"].append(item["style"].lower().replace(" ", "_"))
            if "brand" in item and item["brand"] != "Unknown":
                labels["brands"].append(item["brand"].lower().replace(" ", "_"))
            
            # Extended attributes
            if "occasion_suitability" in item:
                occasions = item["occasion_suitability"] if isinstance(item["occasion_suitability"], list) else [item["occasion_suitability"]]
                labels["occasions"].extend([o.lower().replace(" ", "_") for o in occasions])
            
            if "season_appropriateness" in item:
                seasons = item["season_appropriateness"] if isinstance(item["season_appropriateness"], list) else [item["season_appropriateness"]]
                labels["seasons"].extend([s.lower() for s in seasons])
            
            if "price_range_estimate" in item:
                labels["price_ranges"].append(item["price_range_estimate"].lower().replace(" ", "_"))
            
            if "trend_status" in item:
                labels["trend_status"].append(item["trend_status"].lower())
        
        # Extract from style analysis
        style_analysis = analysis_result.get("advanced_style_analysis", {}).get("style_analysis", {})
        
        if "style_category" in style_analysis:
            labels["styles"].append(style_analysis["style_category"].lower().replace(" ", "_"))
        
        # Create comprehensive tag list
        all_labels = []
        for label_type, label_list in labels.items():
            all_labels.extend(label_list)
        
        labels["tags"] = list(set(all_labels))  # Remove duplicates
        
        # Remove duplicates from all lists
        for key in labels:
            if isinstance(labels[key], list):
                labels[key] = list(set(labels[key]))
        
        return labels

def main():
    """Test the AI Fashion Analyzer"""
    print("🤖 AI Fashion Analyzer Test")
    print("=" * 40)
    
    # Initialize analyzer (you need to provide your API key)
    api_key = "YOUR_GEMINI_API_KEY_HERE"
    
    if api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("Please set your Gemini API key in the script or config file")
        return
    
    analyzer = AIFashionAnalyzer(api_key)
    
    # Test with a sample image
    test_image = "test_image.jpg"  # Replace with actual image path
    
    if Path(test_image).exists():
        result = analyzer.comprehensive_analysis(test_image)
        print(f"Analysis completed for: {test_image}")
        print(f"Fashion items detected: {len(result.get('fashion_items_analysis', {}).get('fashion_items', []))}")
        
        # Extract training labels
        labels = analyzer.extract_training_labels(result)
        print(f"Training labels extracted: {len(labels['tags'])} total tags")
    else:
        print(f"Test image not found: {test_image}")

if __name__ == "__main__":
    main()
