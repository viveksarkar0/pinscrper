import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class PinterestDatabase:
    def __init__(self, db_path: str = "pinterest_pins.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create boards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_url TEXT UNIQUE NOT NULL,
                board_title TEXT,
                board_description TEXT,
                total_pins INTEGER DEFAULT 0,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create pins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER,
                pin_id TEXT UNIQUE,
                pin_url TEXT,
                image_url TEXT,
                title TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES boards (id)
            )
        ''')
        
        # Create ai_labels table with comprehensive fashion analysis fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pin_id INTEGER,
                detected_fashion_items TEXT,  -- JSON string of detected fashion items
                comprehensive_style_analysis TEXT, -- JSON string of style analysis
                color_analysis TEXT, -- JSON string of color analysis
                silhouette_analysis TEXT, -- JSON string of silhouette analysis
                fabric_and_texture_analysis TEXT, -- JSON string of fabric analysis
                styling_techniques TEXT, -- JSON string of styling techniques
                trend_analysis TEXT, -- JSON string of trend analysis
                occasion_analysis TEXT, -- JSON string of occasion analysis
                brand_and_luxury_indicators TEXT, -- JSON string of brand analysis
                personal_style_insights TEXT, -- JSON string of personal style insights
                overall_aesthetic TEXT,
                style_category TEXT,
                confidence_score REAL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pin_id) REFERENCES pins (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pins_board_id ON pins(board_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_labels_pin_id ON ai_labels(pin_id)')
        
        conn.commit()
        conn.close()
    
    def add_board(self, board_url: str, board_title: str = None, board_description: str = None) -> int:
        """Add a new board to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO boards (board_url, board_title, board_description)
                VALUES (?, ?, ?)
            ''', (board_url, board_title, board_description))
            
            # Get the board ID
            cursor.execute('SELECT id FROM boards WHERE board_url = ?', (board_url,))
            board_id = cursor.fetchone()[0]
            
            conn.commit()
            return board_id
        except Exception as e:
            print(f"Error adding board: {e}")
            return None
        finally:
            conn.close()
    
    def add_pin(self, board_id: int, pin_data: Dict) -> int:
        """Add a new pin to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO pins (board_id, pin_id, pin_url, image_url, title, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                board_id,
                pin_data.get('pin_id'),
                pin_data.get('pin_url'),
                pin_data.get('image_url'),
                pin_data.get('title'),
                pin_data.get('description')
            ))
            
            # Get the pin ID
            cursor.execute('SELECT id FROM pins WHERE pin_id = ?', (pin_data.get('pin_id'),))
            result = cursor.fetchone()
            pin_id = result[0] if result else None
            
            conn.commit()
            return pin_id
        except Exception as e:
            print(f"Error adding pin: {e}")
            return None
        finally:
            conn.close()
    
    def add_ai_label(self, pin_id: int, ai_analysis: Dict):
        """Add comprehensive AI analysis results to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract data from the new comprehensive format
            comprehensive_style = ai_analysis.get('comprehensive_style_analysis', {})
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_labels (
                    pin_id, detected_fashion_items, comprehensive_style_analysis, color_analysis,
                    silhouette_analysis, fabric_and_texture_analysis, styling_techniques,
                    trend_analysis, occasion_analysis, brand_and_luxury_indicators,
                    personal_style_insights, overall_aesthetic, style_category, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pin_id,
                json.dumps(ai_analysis.get('detected_fashion_items', [])),
                json.dumps(comprehensive_style),
                json.dumps(ai_analysis.get('color_analysis', {})),
                json.dumps(ai_analysis.get('silhouette_analysis', {})),
                json.dumps(ai_analysis.get('fabric_and_texture_analysis', {})),
                json.dumps(ai_analysis.get('styling_techniques', {})),
                json.dumps(ai_analysis.get('trend_analysis', {})),
                json.dumps(ai_analysis.get('occasion_analysis', {})),
                json.dumps(ai_analysis.get('brand_and_luxury_indicators', {})),
                json.dumps(ai_analysis.get('personal_style_insights', {})),
                comprehensive_style.get('overall_aesthetic', ''),
                comprehensive_style.get('style_category', ''),
                ai_analysis.get('confidence_score', 0.0)
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error adding AI label: {e}")
        finally:
            conn.close()
    
    def get_unlabeled_pins(self, limit: int = 100) -> List[Dict]:
        """Get pins that haven't been processed by AI yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.id, p.pin_id, p.image_url, p.title, p.description
                FROM pins p
                LEFT JOIN ai_labels al ON p.id = al.pin_id
                WHERE al.pin_id IS NULL
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"Error getting unlabeled pins: {e}")
            return []
        finally:
            conn.close()
    
    def get_board_stats(self, board_id: int) -> Dict:
        """Get statistics for a specific board"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    COUNT(p.id) as total_pins,
                    COUNT(al.id) as labeled_pins
                FROM pins p
                LEFT JOIN ai_labels al ON p.id = al.pin_id
                WHERE p.board_id = ?
            ''', (board_id,))
            
            result = cursor.fetchone()
            return {
                'total_pins': result[0],
                'labeled_pins': result[1],
                'unlabeled_pins': result[0] - result[1]
            }
        except Exception as e:
            print(f"Error getting board stats: {e}")
            return {}
        finally:
            conn.close()
    
    def update_board_pin_count(self, board_id: int):
        """Update the total pin count for a board"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE boards 
                SET total_pins = (
                    SELECT COUNT(*) FROM pins WHERE board_id = ?
                )
                WHERE id = ?
            ''', (board_id, board_id))
            
            conn.commit()
        except Exception as e:
            print(f"Error updating board pin count: {e}")
        finally:
            conn.close()
    
    def get_all_pins(self) -> List[Dict]:
        """Get all pins from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.pin_id, p.pin_url, p.image_url, p.title, p.description, 
                       p.scraped_at, b.board_url
                FROM pins p
                LEFT JOIN boards b ON p.board_id = b.id
                ORDER BY p.scraped_at DESC
            ''')
            
            pins = []
            for row in cursor.fetchall():
                pins.append({
                    'pin_id': row[0],
                    'pin_url': row[1],
                    'image_url': row[2],
                    'title': row[3],
                    'description': row[4],
                    'scraped_at': row[5],
                    'board_url': row[6]
                })
            
            return pins
            
        except Exception as e:
            print(f"Error getting all pins: {e}")
            return []
        finally:
            conn.close()
    
    def save_pin(self, pin_data: Dict) -> int:
        """Save a pin to the database (wrapper for add_pin)"""
        try:
            # Get or create board first
            board_url = pin_data.get('board_url')
            if board_url:
                board_id = self.add_board(board_url, '', '')
            else:
                # Use default board if no board URL provided
                board_id = 1
            
            # Add the pin
            return self.add_pin(board_id, pin_data)
            
        except Exception as e:
            print(f"Error saving pin: {e}")
            return None
    
    def save_board(self, board_data: Dict) -> int:
        """Save a board to the database (wrapper for add_board)"""
        try:
            return self.add_board(
                board_data.get('board_url', ''),
                board_data.get('board_title', ''),
                board_data.get('board_description', '')
            )
        except Exception as e:
            print(f"Error saving board: {e}")
            return None
