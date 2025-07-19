#!/usr/bin/env python3
"""
Label Downloaded Images - Complete Fashion Analysis Pipeline
This script demonstrates the complete workflow from downloaded images to AI labeling.
"""

import os
import json
from PIL import Image
from database import PinterestDatabase
from ai_analyzer import FashionAIAnalyzer
from typing import Dict, List
import logging

class ImageLabelingPipeline:
    def __init__(self):
        self.db = PinterestDatabase()
        # Note: AI analyzer requires GEMINI_API_KEY in .env file
        try:
            self.ai_analyzer = FashionAIAnalyzer()
            self.ai_available = True
        except Exception as e:
            print(f"⚠️  AI Analyzer not available: {e}")
            print("💡 To enable AI labeling, add GEMINI_API_KEY to your .env file")
            self.ai_available = False
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_downloaded_images(self) -> List[Dict]:
        """Get list of downloaded images with metadata"""
        images = []
        pins_dir = "downloaded_images/pins"
        
        if not os.path.exists(pins_dir):
            print(f"❌ Download directory not found: {pins_dir}")
            return images
        
        # Get all pins from database
        all_pins = self.db.get_all_pins()
        pin_lookup = {pin['pin_id']: pin for pin in all_pins}
        
        # Check which pins have downloaded images
        for filename in os.listdir(pins_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                # Extract pin_id from filename (format: pin_id_title_hash.jpg)
                pin_id = filename.split('_')[0]
                
                if pin_id in pin_lookup:
                    pin_data = pin_lookup[pin_id]
                    images.append({
                        'filename': filename,
                        'filepath': os.path.join(pins_dir, filename),
                        'pin_id': pin_id,
                        'title': pin_data['title'],
                        'description': pin_data['description'],
                        'pin_url': pin_data['pin_url'],
                        'board_url': pin_data['board_url']
                    })
        
        return images
    
    def analyze_image_basic(self, image_data: Dict) -> Dict:
        """Basic analysis without AI (file info, metadata)"""
        filepath = image_data['filepath']
        
        try:
            # Get image dimensions and file size
            with Image.open(filepath) as img:
                width, height = img.size
                file_size = os.path.getsize(filepath)
                
            analysis = {
                'pin_id': image_data['pin_id'],
                'filename': image_data['filename'],
                'image_info': {
                    'width': width,
                    'height': height,
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2)
                },
                'metadata': {
                    'title': image_data['title'],
                    'description': image_data['description'],
                    'pin_url': image_data['pin_url'],
                    'board_url': image_data['board_url']
                },
                'basic_labels': self.extract_basic_labels(image_data),
                'analysis_type': 'basic'
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {filepath}: {e}")
            return None
    
    def extract_basic_labels(self, image_data: Dict) -> Dict:
        """Extract basic labels from title and description"""
        title = image_data.get('title') or ''
        description = image_data.get('description') or ''
        
        # Handle None values safely
        if title is None:
            title = ''
        if description is None:
            description = ''
            
        title = str(title).lower()
        description = str(description).lower()
        text = f"{title} {description}"
        
        # Basic keyword extraction
        fashion_keywords = {
            'garments': [],
            'styles': [],
            'colors': [],
            'occasions': []
        }
        
        # Garment detection
        garment_words = ['dress', 'shirt', 'pants', 'jeans', 'skirt', 'top', 'jacket', 'coat', 'sweater', 'blouse']
        for word in garment_words:
            if word in text:
                fashion_keywords['garments'].append(word)
        
        # Style detection
        style_words = ['casual', 'formal', 'vintage', 'modern', 'trendy', 'classic', 'boho', 'chic']
        for word in style_words:
            if word in text:
                fashion_keywords['styles'].append(word)
        
        # Color detection
        color_words = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'pink', 'purple', 'brown', 'gray']
        for word in color_words:
            if word in text:
                fashion_keywords['colors'].append(word)
        
        # Occasion detection
        occasion_words = ['party', 'work', 'casual', 'formal', 'wedding', 'summer', 'winter', 'spring', 'fall']
        for word in occasion_words:
            if word in text:
                fashion_keywords['occasions'].append(word)
        
        return fashion_keywords
    
    def analyze_image_ai(self, image_data: Dict) -> Dict:
        """AI-powered analysis using Gemini"""
        if not self.ai_available:
            return None
        
        try:
            filepath = image_data['filepath']
            with Image.open(filepath) as img:
                analysis = self.ai_analyzer.analyze_fashion_image(
                    img, 
                    image_data['title'], 
                    image_data['description']
                )
                analysis['pin_id'] = image_data['pin_id']
                analysis['filename'] = image_data['filename']
                analysis['analysis_type'] = 'ai_powered'
                return analysis
                
        except Exception as e:
            self.logger.error(f"Error in AI analysis for {image_data['filename']}: {e}")
            return None
    
    def save_analysis_to_database(self, analysis: Dict):
        """Save analysis results to database"""
        try:
            # Save to ai_labels table
            self.db.add_ai_label(
                pin_id=analysis['pin_id'],
                detected_fashion_items=json.dumps(analysis.get('fashion_analysis', {})),
                style_analysis=json.dumps(analysis.get('style_analysis', {})),
                color_palette=json.dumps(analysis.get('color_analysis', {})),
                garment_types=json.dumps(analysis.get('garment_types', []))
            )
            self.logger.info(f"Saved analysis for pin {analysis['pin_id']} to database")
            
        except Exception as e:
            self.logger.error(f"Error saving analysis to database: {e}")
    
    def generate_report(self, analyses: List[Dict]) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            'summary': {
                'total_images': len(analyses),
                'successful_analyses': len([a for a in analyses if a is not None]),
                'ai_analyses': len([a for a in analyses if a and a.get('analysis_type') == 'ai_powered']),
                'basic_analyses': len([a for a in analyses if a and a.get('analysis_type') == 'basic'])
            },
            'fashion_insights': {
                'common_garments': {},
                'popular_styles': {},
                'color_distribution': {},
                'occasion_types': {}
            },
            'file_statistics': {
                'total_size_mb': 0,
                'average_dimensions': {'width': 0, 'height': 0},
                'file_formats': {}
            }
        }
        
        # Aggregate insights
        for analysis in analyses:
            if not analysis:
                continue
                
            # File statistics
            if 'image_info' in analysis:
                info = analysis['image_info']
                report['file_statistics']['total_size_mb'] += info.get('file_size_mb', 0)
        
        return report
    
    def run_labeling_pipeline(self, limit: int = None, use_ai: bool = True) -> Dict:
        """Run the complete labeling pipeline"""
        print("🏷️  Starting Image Labeling Pipeline...")
        
        # Get downloaded images
        images = self.get_downloaded_images()
        if not images:
            print("❌ No downloaded images found")
            return {'error': 'No images found'}
        
        if limit:
            images = images[:limit]
        
        print(f"📸 Found {len(images)} downloaded images to analyze")
        
        analyses = []
        for i, image_data in enumerate(images, 1):
            print(f"🔍 Analyzing image {i}/{len(images)}: {image_data['filename']}")
            
            # Try AI analysis first, fall back to basic
            analysis = None
            if use_ai and self.ai_available:
                analysis = self.analyze_image_ai(image_data)
            
            if not analysis:
                analysis = self.analyze_image_basic(image_data)
            
            if analysis:
                analyses.append(analysis)
                # Save to database
                self.save_analysis_to_database(analysis)
                print(f"✅ Analysis complete for {image_data['filename']}")
            else:
                print(f"❌ Failed to analyze {image_data['filename']}")
        
        # Generate report
        report = self.generate_report(analyses)
        
        # Save report to file
        report_filename = f"labeling_report_{len(analyses)}_images.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'report': report,
                'detailed_analyses': analyses
            }, f, indent=2)
        
        print(f"📊 Report saved to: {report_filename}")
        return report

def main():
    """Main function to demonstrate the labeling pipeline"""
    pipeline = ImageLabelingPipeline()
    
    print("🎯 Pinterest Fashion Image Labeling Pipeline")
    print("=" * 50)
    
    # Run pipeline on downloaded images
    report = pipeline.run_labeling_pipeline(limit=10, use_ai=False)  # Start with basic analysis
    
    print("\n📊 LABELING RESULTS:")
    print(f"   Total images processed: {report['summary']['total_images']}")
    print(f"   Successful analyses: {report['summary']['successful_analyses']}")
    print(f"   AI-powered analyses: {report['summary']['ai_analyses']}")
    print(f"   Basic analyses: {report['summary']['basic_analyses']}")
    
    print("\n🎉 Labeling pipeline complete!")
    print("💡 To enable AI-powered analysis, add GEMINI_API_KEY to your .env file")

if __name__ == "__main__":
    main()
