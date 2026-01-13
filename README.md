# Knowledge Base Web Scraper

A Python web scraper designed to extract all content from BetterDocs-powered documentation websites. Automatically discovers categories and articles, then exports data in JSON, Markdown, and CSV formats.

## 🚀 Features

- **🔍 Automatic Discovery** - Automatically finds all categories and articles
- **📊 Progress Tracking** - Real-time progress bars for scraping status
- **🛡️ Error Handling** - Retry logic with exponential backoff
- **⏱️ Rate Limiting** - Respectful delays between requests
- **📦 Multiple Export Formats** - JSON, Markdown, and CSV outputs
- **🎯 Clean Data** - Extracts structured content without HTML clutter

## 📋 Requirements

- Python 3.7 or higher
- Internet connection

## 🔧 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/knowledge-base-scraper.git
cd knowledge-base-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

### Quick Start

1. **Configure your target site** by editing `scraper.py`:

```python
# Open scraper.py and change the base_url in the main() function:
def main():
    scraper = KnowledgeBaseScraper(base_url="https://your-docs-site.com")
    scraper.scrape_all()
    scraper.export_all()
```

2. **Run the scraper**:

```bash
python scraper.py
```

The scraper will:
1. 🔍 Discover all categories from the main docs page
2. 📄 Extract article URLs from each category
3. 💾 Scrape content from each article
4. 📦 Export data in multiple formats to the `output/` folder

### Example Output

```
🚀 Starting scrape of https://your-docs-site.com/docs/

🔍 Discovering categories...
✅ Found 13 categories

📚 Processing categories: 100%|████████████| 13/13
  📄 Category Name: 100%|████████████| 6/6

✅ Scraping complete!
   Categories: 13
   Total Articles: 39

📦 Exporting data...

💾 JSON exported to: output\knowledge_base.json
💾 Markdown files exported to: output\markdown
💾 CSV exported to: output\knowledge_base.csv

✅ All exports complete!

🎉 Done! Check the 'output' folder for results.
```

## 📁 Output Formats

### JSON (`output/knowledge_base.json`)
Structured JSON containing all categories and articles (URLs excluded by default):
```json
{
  "categories": [
    {
      "name": "Category Name",
      "articles": [
        {
          "title": "Article Title",
          "parent_category": "Category Name",
          "content": "Full article content..."
        }
      ]
    }
  ]
}
```

**Note**: URLs are excluded by default. To include them, use:
```python
scraper.export_all(include_urls=True)
```

### Markdown (`output/markdown/`)
Individual markdown files organized by category:
```
output/markdown/
├── policy/
│   ├── student-ambassador.md
│   └── device-policy.md
├── extensions/
│   └── ...
└── ...
```

Each markdown file contains:
- Article title
- Parent category name
- Full article content

**Note**: URLs are excluded by default. To include them in markdown files, use `include_urls=True`.

### CSV (`output/knowledge_base.csv`)
Tabular format with columns (URLs excluded by default):
- Parent Category
- Title
- Content

**With URLs enabled** (`include_urls=True`):
- Parent Category
- Title
- URL
- Content

Perfect for importing into spreadsheets or databases.

## ⚙️ Configuration

You can customize the scraper by editing `scraper.py`:

```python
# Change the base URL
scraper = KnowledgeBaseScraper(base_url="https://your-site.com")

# Adjust rate limiting (in seconds)
time.sleep(1)  # Between categories
time.sleep(0.5)  # Between articles

# Change output directory
scraper.export_all(output_dir="custom_output")

# Include URLs in exports (excluded by default)
scraper.export_all(include_urls=True)

# Modify retry attempts
html = self.get_page(url, retries=5)
```

## 🏗️ Project Structure

```
knowledge-base-scraper/
├── scraper.py          # Main scraper implementation
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── output/            # Generated output (created on first run)
    ├── knowledge_base.json
    ├── knowledge_base.csv
    └── markdown/
```

## 🔍 How It Works

1. **Category Discovery**: Scrapes the main docs page to find all category links
2. **Article Extraction**: For each category, extracts all article URLs
3. **Content Scraping**: Visits each article page and extracts:
   - Title
   - Full text content
   - Parent category information
   - URL (optional)
4. **Export**: Saves data in JSON, Markdown, and CSV formats (URLs excluded by default)

## 🔧 Using with Your BetterDocs Site

### Step 1: Update the Base URL

Open `scraper.py` and modify the `main()` function:

```python
def main():
    # Change this to your documentation site
    scraper = KnowledgeBaseScraper(base_url="https://your-docs-site.com")
    scraper.scrape_all()
    scraper.export_all()
```

### Step 2: Test the Scraper

Run the scraper to see if it works with your site:

```bash
python scraper.py
```

### Step 3: Adjust if Needed

If the scraper doesn't work perfectly, you may need to adjust:

**URL Patterns** - If your site uses custom URLs:
```python
# In extract_categories() method, change:
category_links = soup.find_all('a', href=lambda x: x and '/your-custom-path/' in x)
```

**CSS Selectors** - If your site uses custom HTML classes:
```python
# In extract_article_content() method, add your custom class:
content_div = (
    soup.find('div', class_='your-custom-content-class') or
    soup.find('div', class_='betterdocs-content') or
    soup.find('article')
)
```

**Docs Path** - If your docs aren't at `/docs/`:
```python
# In __init__ method, change:
self.docs_url = f"{base_url}/documentation/"  # or your custom path
```

### Need More Help?

See the **[ADAPTATION_GUIDE.md](ADAPTATION_GUIDE.md)** for detailed instructions on:
- Testing compatibility with your site
- Common issues and solutions
- Advanced customization options
- Step-by-step debugging process

## 📊 Performance

- **Scraping Speed**: Varies by site size (e.g., ~1-2 minutes for 39 articles)
- **Memory Usage**: Minimal - processes articles sequentially
- **Output Size**: Depends on content volume
  - JSON: Compact without URLs
  - CSV: Lightweight tabular format
  - Markdown: Individual files per article

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This scraper is intended for personal use and educational purposes. Always respect the website's `robots.txt` and terms of service. The scraper includes rate limiting to be respectful to the server.

## ☕ Support

If you find this tool useful, consider buying me a coffee!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/gunjanjaswal)

Your support helps me create more open-source tools! 🙏

## 🙏 Acknowledgments

- Built with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- Progress bars powered by [tqdm](https://github.com/tqdm/tqdm)
- Designed for [BetterDocs](https://betterdocs.co/) documentation sites

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Made with ❤️ for documentation enthusiasts**
