#!/usr/bin/env python3
"""
Database Viewer for Pinterest Pin Scraper Pipeline

This script helps you explore and view the contents of your Pinterest pins database.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
import os

class DatabaseViewer:
    def __init__(self, db_path="pinterest_pins.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"❌ Database file '{db_path}' not found!")
            print("Run the pipeline first to create the database.")
            return
        
        self.conn = sqlite3.connect(db_path)
        print(f"✅ Connected to database: {db_path}")
    
    def show_tables(self):
        """Show all tables in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n📊 Database Tables:")
        print("-" * 20)
        for table in tables:
            print(f"• {table[0]}")
    
    def show_stats(self):
        """Show database statistics"""
        cursor = self.conn.cursor()
        
        # Total boards
        cursor.execute("SELECT COUNT(*) FROM boards")
        total_boards = cursor.fetchone()[0]
        
        # Total pins
        cursor.execute("SELECT COUNT(*) FROM pins")
        total_pins = cursor.fetchone()[0]
        
        # Labeled pins
        cursor.execute("SELECT COUNT(*) FROM ai_labels")
        labeled_pins = cursor.fetchone()[0]
        
        # Average confidence score
        cursor.execute("SELECT AVG(confidence_score) FROM ai_labels WHERE confidence_score > 0")
        result = cursor.fetchone()
        avg_confidence = result[0] if result[0] else 0.0
        
        print("\n📈 Database Statistics:")
        print("-" * 25)
        print(f"📁 Total Boards: {total_boards}")
        print(f"📌 Total Pins: {total_pins}")
        print(f"🏷️  Labeled Pins: {labeled_pins}")
        print(f"⏳ Unlabeled Pins: {total_pins - labeled_pins}")
        print(f"🎯 Average Confidence: {avg_confidence:.2f}")
        
        if total_pins > 0:
            completion_rate = (labeled_pins / total_pins) * 100
            print(f"✅ Completion Rate: {completion_rate:.1f}%")
    
    def show_boards(self):
        """Show all boards"""
        df = pd.read_sql_query("SELECT * FROM boards", self.conn)
        
        print("\n📁 Pinterest Boards:")
        print("-" * 30)
        if df.empty:
            print("No boards found.")
        else:
            for _, board in df.iterrows():
                print(f"ID: {board['id']}")
                print(f"Title: {board['board_title'] or 'N/A'}")
                print(f"URL: {board['board_url']}")
                print(f"Total Pins: {board['total_pins']}")
                print(f"Scraped: {board['scraped_at']}")
                print("-" * 30)
    
    def show_recent_pins(self, limit=10):
        """Show recent pins"""
        query = """
        SELECT p.pin_id, p.title, p.image_url, p.scraped_at, b.board_title
        FROM pins p
        JOIN boards b ON p.board_id = b.id
        ORDER BY p.scraped_at DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        
        print(f"\n📌 Recent Pins (Last {limit}):")
        print("-" * 40)
        if df.empty:
            print("No pins found.")
        else:
            for _, pin in df.iterrows():
                print(f"Pin ID: {pin['pin_id']}")
                print(f"Title: {pin['title'][:50] + '...' if pin['title'] and len(pin['title']) > 50 else pin['title'] or 'N/A'}")
                print(f"Board: {pin['board_title'] or 'N/A'}")
                print(f"Scraped: {pin['scraped_at']}")
                print("-" * 40)
    
    def show_ai_analysis_sample(self, limit=5):
        """Show sample AI analysis results"""
        query = """
        SELECT p.pin_id, p.title, al.overall_aesthetic, al.style_category, 
               al.confidence_score, al.processed_at
        FROM ai_labels al
        JOIN pins p ON al.pin_id = p.id
        ORDER BY al.processed_at DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        
        print(f"\n🤖 AI Analysis Sample (Last {limit}):")
        print("-" * 50)
        if df.empty:
            print("No AI analysis found.")
        else:
            for _, analysis in df.iterrows():
                print(f"Pin ID: {analysis['pin_id']}")
                print(f"Title: {analysis['title'][:40] + '...' if analysis['title'] and len(analysis['title']) > 40 else analysis['title'] or 'N/A'}")
                print(f"Style Category: {analysis['style_category'] or 'N/A'}")
                print(f"Aesthetic: {analysis['overall_aesthetic'][:60] + '...' if analysis['overall_aesthetic'] and len(analysis['overall_aesthetic']) > 60 else analysis['overall_aesthetic'] or 'N/A'}")
                print(f"Confidence: {analysis['confidence_score']:.2f}")
                print(f"Analyzed: {analysis['processed_at']}")
                print("-" * 50)
    
    def search_pins(self, keyword):
        """Search pins by keyword"""
        query = """
        SELECT p.pin_id, p.title, p.description, b.board_title
        FROM pins p
        JOIN boards b ON p.board_id = b.id
        WHERE p.title LIKE ? OR p.description LIKE ?
        """
        
        search_term = f"%{keyword}%"
        df = pd.read_sql_query(query, self.conn, params=(search_term, search_term))
        
        print(f"\n🔍 Search Results for '{keyword}':")
        print("-" * 40)
        if df.empty:
            print("No pins found matching the keyword.")
        else:
            for _, pin in df.iterrows():
                print(f"Pin ID: {pin['pin_id']}")
                print(f"Title: {pin['title'] or 'N/A'}")
                print(f"Board: {pin['board_title'] or 'N/A'}")
                print("-" * 40)
    
    def export_to_csv(self, table_name, filename=None):
        """Export table to CSV"""
        if not filename:
            filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.conn)
            df.to_csv(filename, index=False)
            print(f"✅ Exported {table_name} to {filename}")
        except Exception as e:
            print(f"❌ Error exporting {table_name}: {e}")
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function with interactive menu"""
    viewer = DatabaseViewer()
    
    if not hasattr(viewer, 'conn'):
        return
    
    while True:
        print("\n" + "="*50)
        print("📊 Pinterest Database Viewer")
        print("="*50)
        print("1. Show database statistics")
        print("2. Show all boards")
        print("3. Show recent pins")
        print("4. Show AI analysis sample")
        print("5. Search pins by keyword")
        print("6. Export table to CSV")
        print("7. Show tables")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            viewer.show_stats()
        elif choice == "2":
            viewer.show_boards()
        elif choice == "3":
            limit = input("How many recent pins to show? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            viewer.show_recent_pins(limit)
        elif choice == "4":
            limit = input("How many AI analysis samples to show? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            viewer.show_ai_analysis_sample(limit)
        elif choice == "5":
            keyword = input("Enter keyword to search: ").strip()
            if keyword:
                viewer.search_pins(keyword)
        elif choice == "6":
            table = input("Enter table name (boards/pins/ai_labels): ").strip()
            if table in ['boards', 'pins', 'ai_labels']:
                viewer.export_to_csv(table)
            else:
                print("Invalid table name!")
        elif choice == "7":
            viewer.show_tables()
        else:
            print("Invalid choice!")
    
    viewer.close()
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()
