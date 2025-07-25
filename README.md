# Pinterest Scraper REST API with AI Fashion Analysis

A production-ready REST API for Pinterest scraping with AI-powered fashion analysis, MongoDB storage, and AWS deployment capabilities. Extract fashion data from Pinterest boards and get comprehensive AI analysis through RESTful endpoints.

## 🚀 Features

- **Production-Ready**: Anti-bot detection measures, rate limiting, error handling
- **AI-Powered**: Advanced fashion analysis using Google Gemini AI
- **Batch Processing**: Scrape multiple boards with concurrent image processing
- **Training Dataset**: Generates ML-ready datasets with structured labels
- **Ban-Proof**: Uses undetected-chromedriver, proxy rotation, and human-like behavior
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## 📋 Requirements

- Python 3.8+
- Chrome browser
- Pinterest account (optional but recommended)
- Google Gemini API key

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   python setup.py
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials:**
   
   Edit `config.json` and add your credentials:
   ```json
   {
     "gemini_api_key": "your_gemini_api_key_here",
     "pinterest_email": "your_email@example.com",
     "pinterest_password": "your_password",
     "board_urls": [
       "https://www.pinterest.com/username/board-name/"
     ]
   }
   ```

## 📖 Usage

### Basic Usage

1. **Add board URLs to `example_boards.txt`:**
   ```
   https://www.pinterest.com/fashionista/street-style/
   https://www.pinterest.com/styleblogger/casual-outfits/
   ```

2. **Run the scraper:**
   ```bash
   python run_scraper.py --boards example_boards.txt
   ```

### Advanced Usage

```bash
# Scrape specific boards with custom settings
python run_scraper.py \
  --url "https://www.pinterest.com/user/board1/" \
  --url "https://www.pinterest.com/user/board2/" \
  --max-pins 50 \
  --headless \
  --output-dir my_dataset

# Test configuration without scraping
python run_scraper.py --dry-run

# Skip AI analysis (faster scraping)
python run_scraper.py --boards boards.txt --no-ai
```

### Command Line Options

- `--config`: Configuration file path (default: config.json)
- `--boards`: Text file with board URLs (one per line)
- `--url`: Single board URL (can be used multiple times)
- `--max-pins`: Maximum pins per board
- `--headless`: Run browser in headless mode
- `--no-ai`: Skip AI analysis
- `--output-dir`: Output directory for scraped data
- `--dry-run`: Test configuration without scraping

## 📁 Output Structure

```
scraped_data/
├── images/                    # Downloaded images
│   ├── pin_id_1.jpg
│   └── pin_id_2.jpg
├── pinterest_data.json        # Raw scraped data
├── training_dataset.json      # ML-ready dataset
├── dataset_manifest.json      # Dataset metadata
└── scraper.log               # Detailed logs
```

## 🤖 AI Analysis Features

The scraper uses Google Gemini AI to analyze each image and extract:

### Fashion Item Detection
- Categories (Clothing, Footwear, Accessories, Bags)
- Specific types (T-shirt, Jeans, Sneakers, etc.)
- Colors and materials
- Brand identification
- Style classification

### Advanced Style Analysis
- Overall aesthetic and style category
- Color harmony and psychology
- Silhouette and proportion analysis
- Trend analysis and forecasting
- Occasion and season suitability
- Price range estimation
- Influencer style matching

### Training Labels
Automatically generates ML training labels:
- Categories, types, colors, materials
- Style tags and attributes
- Occasion and seasonal tags
- Comprehensive tag vocabulary

## ⚙️ Configuration

### config.json Options

```json
{
  "output_dir": "scraped_data",
  "images_dir": "images",
  "max_pins_per_board": 100,
  "request_delay": 2,
  "max_workers": 3,
  "headless": false,
  "use_undetected_chrome": true,
  "gemini_api_key": "your_api_key",
  "pinterest_email": "your_email",
  "pinterest_password": "your_password",
  "proxy_list": [
    "http://proxy1:port",
    "http://proxy2:port"
  ]
}
```

### Anti-Bot Measures

- **Undetected ChromeDriver**: Bypasses basic bot detection
- **Random User Agents**: Rotates browser fingerprints
- **Human-like Delays**: Random delays between actions
- **Rate Limiting**: Configurable request delays
- **Proxy Support**: Rotate through proxy servers
- **Session Management**: Maintains login state

## 🔧 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   pip install webdriver-manager
   python setup.py
   ```

2. **Pinterest Login Failed**
   - Check credentials in config.json
   - Try logging in manually first
   - Use 2FA app passwords if enabled

3. **AI Analysis Errors**
   - Verify Gemini API key
   - Check API quota limits
   - Use --no-ai flag to skip analysis

4. **Bot Detection**
   - Enable headless mode: `--headless`
   - Add proxy servers to config
   - Increase request delays
   - Use different Pinterest account

### Logs and Debugging

Check `scraper.log` for detailed information:
```bash
tail -f scraper.log
```

## 📊 Dataset Format

### Training Dataset Structure

```json
{
  "metadata": {
    "total_samples": 150,
    "created_at": "2024-01-15T10:30:00",
    "description": "Pinterest fashion dataset with AI analysis"
  },
  "samples": [
    {
      "image_path": "images/pin_123.jpg",
      "image_id": "pin_123",
      "title": "Casual Street Style",
      "description": "Comfortable outfit for daily wear",
      "labels": [
        {
          "category": "Clothing",
          "type": "T-shirt",
          "color": ["white", "navy"],
          "material": "Cotton",
          "style": "Casual"
        }
      ],
      "tags": ["clothing", "t_shirt", "white", "navy", "cotton", "casual"]
    }
  ]
}
```

## 🚨 Legal and Ethical Considerations

- **Respect Pinterest's Terms of Service**
- **Use reasonable rate limits** to avoid overloading servers
- **Only scrape public content**
- **Respect copyright** - use data for research/personal use
- **Consider Pinterest's robots.txt**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect Pinterest's terms of service and copyright laws.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review the logs in `scraper.log`
3. Ensure all dependencies are installed
4. Verify your configuration settings

## 🔄 Updates and Maintenance

The scraper includes mechanisms to handle:
- Pinterest UI changes
- Anti-bot measure updates
- API changes
- Chrome/ChromeDriver updates

Regular updates may be needed as Pinterest evolves their platform.

---

**Happy Scraping! 🎨👗👠**
