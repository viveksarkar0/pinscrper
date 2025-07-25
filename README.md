# Pinterest Scraper with AI Fashion Analysis

A comprehensive production-ready Pinterest scraping system with advanced AI-powered fashion analysis capabilities. Extract fashion data from Pinterest boards and get detailed stylist-level analysis using Google Gemini AI.

## 🚀 Key Features

- **Production-Ready Architecture**: Anti-bot detection measures, rate limiting, comprehensive error handling
- **Advanced AI Fashion Analysis**: Stylist-level analysis with trend identification using Google Gemini AI
- **Robust Anti-Bot Protection**: Undetected ChromeDriver, user agent rotation, proxy support, human-like behavior
- **Batch Processing**: Concurrent scraping of multiple boards with intelligent image processing
- **ML Training Dataset Generation**: Structured datasets ready for machine learning model training
- **REST API Ready**: Built with scalable architecture for API deployment
- **Comprehensive Logging**: Detailed monitoring, debugging, and progress tracking
- **AWS Deployment Ready**: Includes Docker, ECS, and CloudFormation configurations

## 📁 Project Structure

```
webscrperinterest/
├── api/                          # REST API components
│   ├── __init__.py
│   └── routes.py                 # API endpoints
├── aws/                          # AWS deployment configs
│   ├── cloudformation.yml        # Infrastructure as code
│   └── ecs-task-definition.json  # ECS container definition
├── core/                         # Core scraping logic
│   ├── pinterest_scraper.py      # Main scraper with anti-bot measures
│   ├── ai_fashion_analyzer.py    # Enhanced AI analysis engine
│   └── run_scraper.py           # Command-line interface
├── config/                       # Configuration files
│   ├── config.json              # Main configuration
│   └── example_boards.txt       # Sample board URLs
├── requirements.txt             # Python dependencies
├── setup.py                     # Automated setup script
├── docker-compose.yml           # Local development setup
├── nginx.conf                   # Web server configuration
└── README.md                    # This file
```

## 📋 Requirements

- **Python 3.8+**
- **Chrome browser** (latest version recommended)
- **Pinterest account** (optional but recommended for better access)
- **Google Gemini API key** (for AI fashion analysis)
- **4GB+ RAM** (for concurrent processing)

## 🛠️ Quick Setup

### 1. Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd webscrperinterest

# Run automated setup
python setup.py
```

### 2. Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config/config.json.example config/config.json
# Edit config.json with your credentials
```

### 3. Configuration

Edit `config/config.json`:
```json
{
  "gemini_api_key": "your_gemini_api_key_here",
  "pinterest_email": "your_email@example.com",
  "pinterest_password": "your_password",
  "output_dir": "scraped_data",
  "max_pins_per_board": 100,
  "request_delay": 2,
  "max_workers": 3,
  "headless": false,
  "use_undetected_chrome": true,
  "proxy_list": []
}
```

## 📖 Usage

### Command Line Interface

#### Basic Usage
```bash
# Scrape from board URLs file
python core/run_scraper.py --boards config/example_boards.txt

# Scrape specific boards
python core/run_scraper.py \
  --url "https://www.pinterest.com/user/fashion-board/" \
  --url "https://www.pinterest.com/user/style-board/" \
  --max-pins 50
```

#### Advanced Options
```bash
# Production scraping with all features
python core/run_scraper.py \
  --boards config/boards.txt \
  --max-pins 200 \
  --headless \
  --output-dir production_dataset \
  --config config/production.json

# Fast scraping without AI analysis
python core/run_scraper.py \
  --boards config/boards.txt \
  --no-ai \
  --max-workers 5

# Test configuration
python core/run_scraper.py --dry-run --config config/config.json
```

#### Command Line Options
- `--config`: Configuration file path (default: config/config.json)
- `--boards`: Text file with board URLs (one per line)
- `--url`: Single board URL (can be used multiple times)
- `--max-pins`: Maximum pins per board (default: 100)
- `--headless`: Run browser in headless mode
- `--no-ai`: Skip AI analysis for faster scraping
- `--output-dir`: Custom output directory
- `--max-workers`: Number of concurrent workers
- `--dry-run`: Test configuration without actual scraping

### REST API Usage (Future)
```bash
# Start the API server
python api/app.py

# Example API calls
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"board_url": "https://www.pinterest.com/user/board/"}'
```

## 🤖 AI Fashion Analysis Features

### Enhanced Analysis Capabilities
- **Fashion Item Detection**: Categories, types, colors, materials, brands
- **Style Analysis**: Aesthetic classification, trend identification, style matching
- **Color Psychology**: Color harmony analysis and emotional impact
- **Trend Forecasting**: Emerging trend identification and popularity prediction
- **Occasion Matching**: Appropriate settings and seasonal suitability
- **Price Estimation**: Market value analysis based on visual cues
- **Influencer Style Matching**: Celebrity and influencer style comparisons

### Analysis Output Structure
```json
{
  "fashion_items": [
    {
      "category": "Clothing",
      "type": "Blazer",
      "color": ["navy", "dark_blue"],
      "material": "Wool blend",
      "brand": "Estimated: Premium",
      "style": "Business casual",
      "confidence": 0.92
    }
  ],
  "style_analysis": {
    "overall_aesthetic": "Modern professional",
    "style_category": "Business casual",
    "trend_alignment": "Contemporary classic",
    "season": "Fall/Winter",
    "occasion": ["Work", "Business meetings", "Professional events"]
  },
  "color_analysis": {
    "dominant_colors": ["navy", "white", "silver"],
    "color_harmony": "Monochromatic with accent",
    "color_psychology": "Professional, trustworthy, sophisticated"
  },
  "trend_analysis": {
    "current_trends": ["Oversized blazers", "Neutral tones", "Minimalist styling"],
    "trend_score": 8.5,
    "emerging_elements": ["Sustainable fabrics", "Gender-neutral cuts"]
  }
}
```

## 📊 Output Structure

```
scraped_data/
├── images/                    # Downloaded images organized by board
│   ├── board_1/
│   │   ├── pin_123456.jpg
│   │   └── pin_789012.jpg
│   └── board_2/
├── data/                      # Structured data files
│   ├── pinterest_data.json    # Raw scraped data
│   ├── training_dataset.json  # ML-ready dataset with labels
│   ├── dataset_manifest.json  # Dataset metadata and statistics
│   └── analysis_summary.json  # AI analysis summary
├── logs/                      # Comprehensive logging
│   ├── scraper.log           # Main scraper logs
│   ├── ai_analysis.log       # AI processing logs
│   └── error.log             # Error tracking
└── exports/                   # Export formats
    ├── csv_export.csv        # Tabular data export
    └── training_labels.json  # ML training labels
```

## 🛡️ Anti-Bot Protection

### Implemented Measures
- **Undetected ChromeDriver**: Advanced bot detection bypass
- **Dynamic User Agent Rotation**: Randomized browser fingerprints
- **Human-like Behavior Simulation**: Random delays, mouse movements, scrolling
- **Proxy Rotation Support**: Multiple proxy server integration
- **Session Management**: Persistent login state maintenance
- **Rate Limiting**: Intelligent request throttling
- **CAPTCHA Handling**: Manual intervention prompts when needed

### Configuration
```json
{
  "anti_bot_measures": {
    "use_undetected_chrome": true,
    "rotate_user_agents": true,
    "human_delays": {
      "min": 1,
      "max": 5
    },
    "proxy_rotation": true,
    "max_requests_per_minute": 30
  }
}
```

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. ChromeDriver Issues
```bash
# Update ChromeDriver automatically
python setup.py --update-chrome

# Manual installation
pip install webdriver-manager
```

#### 2. Pinterest Login Problems
- Verify credentials in `config/config.json`
- Check for 2FA requirements (use app passwords)
- Try manual login first to verify account status
- Check for account restrictions or temporary blocks

#### 3. AI Analysis Errors
```bash
# Verify API key
python -c "from core.ai_fashion_analyzer import test_api_key; test_api_key()"

# Check API quota
# Monitor usage at https://console.cloud.google.com/
```

#### 4. Bot Detection Issues
- Enable headless mode: `--headless`
- Add proxy servers to configuration
- Increase request delays in config
- Use different Pinterest account
- Clear browser data and cookies

#### 5. Memory Issues
- Reduce `max_workers` in configuration
- Process smaller batches
- Enable image compression
- Monitor system resources

### Debug Mode
```bash
# Enable verbose logging
python core/run_scraper.py --debug --boards config/test_boards.txt

# Check specific component
python core/pinterest_scraper.py --test
python core/ai_fashion_analyzer.py --test
```

## 📈 Performance Optimization

### Recommended Settings
```json
{
  "performance": {
    "max_workers": 3,
    "request_delay": 2,
    "image_quality": "medium",
    "batch_size": 50,
    "memory_limit": "2GB"
  }
}
```

### Scaling Guidelines
- **Small datasets (< 1000 images)**: 2-3 workers, 1-2s delay
- **Medium datasets (1000-5000 images)**: 3-4 workers, 2-3s delay  
- **Large datasets (> 5000 images)**: 4-5 workers, 3-5s delay, use proxies

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale scraper=3
```

### AWS ECS Deployment
```bash
# Deploy using CloudFormation
aws cloudformation create-stack \
  --stack-name pinterest-scraper \
  --template-body file://aws/cloudformation.yml \
  --parameters ParameterKey=ImageTag,ParameterValue=latest
```

## 📊 Dataset Quality

### Training Dataset Features
- **Structured Labels**: Comprehensive fashion taxonomy
- **Quality Scores**: AI confidence ratings for each analysis
- **Metadata**: Image dimensions, source URLs, scraping timestamps
- **Validation**: Automated quality checks and duplicate detection
- **Export Formats**: JSON, CSV, TensorFlow Records

### Dataset Statistics
The system automatically generates dataset statistics including:
- Total samples and unique items
- Category distribution
- Color and style analysis
- Quality metrics and confidence scores

## 🚨 Legal & Ethical Guidelines

### Best Practices
- **Respect Pinterest's Terms of Service** and rate limits
- **Use reasonable delays** to avoid server overload
- **Only scrape publicly available content**
- **Respect copyright and intellectual property rights**
- **Use data responsibly** for research and educational purposes
- **Consider Pinterest's robots.txt** guidelines

### Compliance Features
- Built-in rate limiting and respectful scraping practices
- User-agent identification for transparency
- Configurable delays and request throttling
- Comprehensive logging for audit trails

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes** with proper testing
4. **Follow code style guidelines** (PEP 8 for Python)
5. **Add tests** for new functionality
6. **Update documentation** as needed
7. **Submit a pull request** with detailed description

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black core/ api/
flake8 core/ api/
```

## 📄 License

This project is intended for educational and research purposes. Users are responsible for complying with Pinterest's Terms of Service and applicable copyright laws.

## 🆘 Support & Maintenance

### Getting Help
1. **Check the troubleshooting section** above
2. **Review logs** in the `logs/` directory
3. **Verify configuration** settings
4. **Test with minimal examples** first
5. **Check system requirements** and dependencies

### Regular Maintenance
The scraper includes mechanisms to handle:
- Pinterest UI changes and updates
- Anti-bot measure evolution
- Chrome/ChromeDriver version updates
- API changes and deprecations

### Update Notifications
Monitor the repository for updates addressing:
- Pinterest platform changes
- Security improvements
- New AI analysis features
- Performance optimizations

---

**Happy Fashion Data Mining! 🎨👗👠✨**

*Built with ❤️ for the fashion AI community*
