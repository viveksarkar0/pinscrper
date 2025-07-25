#!/usr/bin/env python3
"""
Pinterest Database Viewer
View and explore scraped Pinterest data
"""

import json
import os
from datetime import datetime
from pathlib import Path
import sys

def load_scraped_pins_tracker():
    """Load the scraped pins tracker"""
    tracker_file = 'scraped_pins_tracker.json'
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r') as f:
            return json.load(f)
    return {}

def load_dataset():
    """Load the complete dataset"""
    dataset_file = 'scraped_data/pinterest_dataset.jsonl'
    pins = []
    
    if os.path.exists(dataset_file):
        with open(dataset_file, 'r') as f:
            for line in f:
                if line.strip():
                    pins.append(json.loads(line))
    
    return pins

def show_overview():
    """Show database overview"""
    print("📊 Pinterest Database Overview")
    print("=" * 40)
    
    # Load tracker data
    tracker = load_scraped_pins_tracker()
    total_pins = tracker.get('total_pins', 0)
    last_updated = tracker.get('last_updated', 'Never')
    
    print(f"📌 Total pins scraped: {total_pins}")
    print(f"🕒 Last updated: {last_updated}")
    
    # Check scraped_data directory
    scraped_dir = Path('scraped_data')
    if scraped_dir.exists():
        json_files = list(scraped_dir.glob('pin_*.json'))
        dataset_file = scraped_dir / 'pinterest_dataset.jsonl'
        
        print(f"📁 Individual pin files: {len(json_files)}")
        print(f"📄 Dataset file: {'✅ Exists' if dataset_file.exists() else '❌ Missing'}")
        
        if dataset_file.exists():
            size_mb = dataset_file.stat().st_size / (1024 * 1024)
            print(f"💾 Dataset size: {size_mb:.2f} MB")
    else:
        print("📁 No scraped_data directory found")

def show_recent_pins(limit=10):
    """Show recent pins"""
    print(f"\n📌 Recent {limit} Pins")
    print("=" * 30)
    
    pins = load_dataset()
    
    if not pins:
        print("❌ No pins found in database")
        return
    
    # Sort by scraped_at timestamp (most recent first)
    pins_sorted = sorted(pins, key=lambda x: x.get('scraped_at', ''), reverse=True)
    
    for i, pin in enumerate(pins_sorted[:limit], 1):
        print(f"\n{i}. Pin ID: {pin.get('pin_id', 'Unknown')}")
        print(f"   Title: {pin.get('title', 'No title')}")
        print(f"   Board: {pin.get('board_name', 'Unknown board')}")
        print(f"   URL: {pin.get('url', 'No URL')}")
        print(f"   Scraped: {pin.get('scraped_at', 'Unknown time')}")
        
        # Show AI analysis if available
        ai_analysis = pin.get('ai_analysis')
        if ai_analysis:
            print(f"   🤖 AI Analysis: {ai_analysis.get('style', 'N/A')} style, {len(ai_analysis.get('colors', []))} colors")

def show_board_statistics():
    """Show statistics by board"""
    print("\n📋 Board Statistics")
    print("=" * 25)
    
    pins = load_dataset()
    
    if not pins:
        print("❌ No pins found in database")
        return
    
    # Count pins by board
    board_counts = {}
    for pin in pins:
        board_name = pin.get('board_name', 'Unknown')
        board_counts[board_name] = board_counts.get(board_name, 0) + 1
    
    # Sort by count
    sorted_boards = sorted(board_counts.items(), key=lambda x: x[1], reverse=True)
    
    for board, count in sorted_boards:
        print(f"📌 {board}: {count} pins")

def show_ai_analysis_summary():
    """Show AI analysis summary"""
    print("\n🤖 AI Analysis Summary")
    print("=" * 30)
    
    pins = load_dataset()
    
    if not pins:
        print("❌ No pins found in database")
        return
    
    analyzed_pins = [pin for pin in pins if pin.get('ai_analysis')]
    
    print(f"📊 Pins with AI analysis: {len(analyzed_pins)}/{len(pins)}")
    
    if not analyzed_pins:
        print("❌ No AI analysis data found")
        return
    
    # Collect style statistics
    styles = {}
    colors = {}
    
    for pin in analyzed_pins:
        ai_data = pin.get('ai_analysis', {})
        
        # Count styles
        style = ai_data.get('style', 'Unknown')
        styles[style] = styles.get(style, 0) + 1
        
        # Count colors
        pin_colors = ai_data.get('colors', [])
        for color in pin_colors:
            colors[color] = colors.get(color, 0) + 1
    
    # Show top styles
    print("\n🎨 Top Styles:")
    for style, count in sorted(styles.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {style}: {count} pins")
    
    # Show top colors
    print("\n🌈 Top Colors:")
    for color, count in sorted(colors.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {color}: {count} pins")

def search_pins(query):
    """Search pins by title or description"""
    print(f"\n🔍 Search Results for '{query}'")
    print("=" * 30)
    
    pins = load_dataset()
    
    if not pins:
        print("❌ No pins found in database")
        return
    
    # Search in title and description
    matching_pins = []
    query_lower = query.lower()
    
    for pin in pins:
        title = pin.get('title', '').lower()
        description = pin.get('description', '').lower()
        
        if query_lower in title or query_lower in description:
            matching_pins.append(pin)
    
    if not matching_pins:
        print(f"❌ No pins found matching '{query}'")
        return
    
    print(f"✅ Found {len(matching_pins)} matching pins:")
    
    for i, pin in enumerate(matching_pins, 1):
        print(f"\n{i}. {pin.get('title', 'No title')}")
        print(f"   Board: {pin.get('board_name', 'Unknown')}")
        print(f"   Description: {pin.get('description', 'No description')[:100]}...")

def export_to_csv():
    """Export data to CSV format"""
    print("\n📤 Exporting to CSV")
    print("=" * 20)
    
    pins = load_dataset()
    
    if not pins:
        print("❌ No pins found in database")
        return
    
    import csv
    
    csv_file = 'pinterest_export.csv'
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if pins:
            # Get all possible field names
            fieldnames = set()
            for pin in pins:
                fieldnames.update(pin.keys())
                if pin.get('ai_analysis'):
                    ai_fields = pin['ai_analysis'].keys()
                    fieldnames.update([f'ai_{field}' for field in ai_fields])
            
            fieldnames = sorted(list(fieldnames))
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for pin in pins:
                row = pin.copy()
                
                # Flatten AI analysis
                if pin.get('ai_analysis'):
                    for key, value in pin['ai_analysis'].items():
                        row[f'ai_{key}'] = value
                    del row['ai_analysis']
                
                # Convert lists to strings
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = ', '.join(map(str, value))
                
                writer.writerow(row)
    
    print(f"✅ Exported {len(pins)} pins to {csv_file}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🎯 Pinterest Database Viewer")
        print("=" * 30)
        print("Commands:")
        print("  overview     - Show database overview")
        print("  recent [N]   - Show N recent pins (default: 10)")
        print("  boards       - Show statistics by board")
        print("  ai           - Show AI analysis summary")
        print("  search TERM  - Search pins by title/description")
        print("  export       - Export data to CSV")
        print("  all          - Show all information")
        print()
        print("Examples:")
        print("  python3 view_database.py overview")
        print("  python3 view_database.py recent 5")
        print("  python3 view_database.py search fashion")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'overview':
        show_overview()
    elif command == 'recent':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_recent_pins(limit)
    elif command == 'boards':
        show_board_statistics()
    elif command == 'ai':
        show_ai_analysis_summary()
    elif command == 'search':
        if len(sys.argv) < 3:
            print("❌ Please provide a search term")
            return
        query = ' '.join(sys.argv[2:])
        search_pins(query)
    elif command == 'export':
        export_to_csv()
    elif command == 'all':
        show_overview()
        show_recent_pins(5)
        show_board_statistics()
        show_ai_analysis_summary()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
