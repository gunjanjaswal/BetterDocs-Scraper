#!/usr/bin/env python3
"""
Knowledge Base Web Scraper
Scrapes all content from https://knowledgebase.believersdestination.com/docs/
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import os
import time
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urljoin, urlparse

class KnowledgeBaseScraper:
    def __init__(self, base_url="https://your-docs-site.com"):
        """
        Initialize the scraper with your BetterDocs-powered documentation site.
        
        Args:
            base_url: The base URL of your documentation site (e.g., "https://docs.example.com")
        """
        self.base_url = base_url
        self.docs_url = f"{base_url}/docs/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.data = {
            "base_url": base_url,
            "categories": []
        }
        
    def get_page(self, url, retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(f"\n❌ Failed to fetch {url}: {e}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def extract_categories(self):
        """Extract all category links from the main docs page"""
        print("🔍 Discovering categories...")
        html = self.get_page(self.docs_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        categories = []
        
        # Find all category cards - they typically have "Explore More" buttons
        category_links = soup.find_all('a', href=lambda x: x and '/docs-category/' in x)
        
        seen_urls = set()
        for link in category_links:
            url = urljoin(self.base_url, link.get('href'))
            if url not in seen_urls:
                seen_urls.add(url)
                # Extract category name from URL or link text
                category_name = link.get_text(strip=True) or url.split('/')[-2]
                categories.append({
                    'name': category_name,
                    'url': url,
                    'articles': []
                })
        
        print(f"✅ Found {len(categories)} categories")
        return categories
    
    def extract_articles_from_category(self, category_url):
        """Extract all article links from a category page"""
        html = self.get_page(category_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        # Find all article links
        article_links = soup.find_all('a', href=lambda x: x and '/docs/' in x and '/docs-category/' not in x)
        
        seen_urls = set()
        for link in article_links:
            url = urljoin(self.base_url, link.get('href'))
            # Avoid duplicates and the main docs page
            if url not in seen_urls and url != self.docs_url:
                seen_urls.add(url)
                articles.append(url)
        
        return articles
    
    def extract_article_content(self, article_url, category_name):
        """Extract content from an article page"""
        html = self.get_page(article_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Untitled"
        
        # Extract main content - BetterDocs typically uses specific classes
        content_div = (
            soup.find('div', class_='betterdocs-content') or
            soup.find('article') or
            soup.find('div', class_='entry-content') or
            soup.find('main')
        )
        
        if content_div:
            # Remove script and style elements
            for script in content_div(['script', 'style', 'nav']):
                script.decompose()
            
            # Get text content
            content_text = content_div.get_text(separator='\n', strip=True)
            
            # Get HTML content for markdown conversion
            content_html = str(content_div)
        else:
            content_text = "Content not found"
            content_html = ""
        
        return {
            'title': title_text,
            'url': article_url,
            'category': category_name,
            'content': content_text,
            'html': content_html
        }
    
    def scrape_all(self):
        """Main scraping function"""
        print(f"\n🚀 Starting scrape of {self.docs_url}\n")
        
        # Step 1: Get all categories
        categories = self.extract_categories()
        if not categories:
            print("❌ No categories found. Exiting.")
            return
        
        # Step 2: For each category, get articles
        for category in tqdm(categories, desc="📚 Processing categories"):
            time.sleep(1)  # Be respectful to the server
            
            article_urls = self.extract_articles_from_category(category['url'])
            
            # Step 3: For each article, extract content
            for article_url in tqdm(article_urls, desc=f"  📄 {category['name']}", leave=False):
                time.sleep(0.5)  # Rate limiting
                
                article_data = self.extract_article_content(article_url, category['name'])
                if article_data:
                    category['articles'].append(article_data)
            
            # Update the main data structure
            self.data['categories'].append(category)
        
        # Print summary
        total_articles = sum(len(cat['articles']) for cat in self.data['categories'])
        print(f"\n✅ Scraping complete!")
        print(f"   Categories: {len(self.data['categories'])}")
        print(f"   Total Articles: {total_articles}")
        
        return self.data
    
    def export_json(self, output_dir="output"):
        """Export data as JSON"""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / "knowledge_base.json"
        
        # Create a clean version without HTML
        clean_data = {
            "base_url": self.data["base_url"],
            "categories": []
        }
        
        for category in self.data['categories']:
            clean_category = {
                "name": category['name'],
                "url": category['url'],
                "articles": []
            }
            for article in category['articles']:
                clean_category['articles'].append({
                    'title': article['title'],
                    'url': article['url'],
                    'category': article['category'],
                    'content': article['content']
                })
            clean_data['categories'].append(clean_category)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON exported to: {filepath}")
    
    def export_markdown(self, output_dir="output"):
        """Export articles as individual markdown files organized by category"""
        base_path = Path(output_dir) / "markdown"
        base_path.mkdir(parents=True, exist_ok=True)
        
        for category in self.data['categories']:
            # Create category folder
            category_slug = category['name'].lower().replace(' ', '-').replace('/', '-')
            category_path = base_path / category_slug
            category_path.mkdir(exist_ok=True)
            
            for article in category['articles']:
                # Create filename from title
                filename = article['title'].lower().replace(' ', '-').replace('/', '-')
                filename = ''.join(c for c in filename if c.isalnum() or c == '-')
                filepath = category_path / f"{filename}.md"
                
                # Create markdown content
                md_content = f"""# {article['title']}

**Category:** {article['category']}  
**URL:** {article['url']}

---

{article['content']}
"""
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
        
        print(f"💾 Markdown files exported to: {base_path}")
    
    def export_csv(self, output_dir="output"):
        """Export data as CSV"""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / "knowledge_base.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Title', 'URL', 'Content'])
            
            for category in self.data['categories']:
                for article in category['articles']:
                    writer.writerow([
                        article['category'],
                        article['title'],
                        article['url'],
                        article['content']
                    ])
        
        print(f"💾 CSV exported to: {filepath}")
    
    def export_all(self, output_dir="output"):
        """Export in all formats"""
        print(f"\n📦 Exporting data...\n")
        self.export_json(output_dir)
        self.export_markdown(output_dir)
        self.export_csv(output_dir)
        print(f"\n✅ All exports complete!")


def main():
    # CONFIGURE YOUR SITE HERE
    # Replace with your BetterDocs-powered documentation site URL
    scraper = KnowledgeBaseScraper(base_url="https://your-docs-site.com")
    
    # Scrape all content
    scraper.scrape_all()
    
    # Export in all formats
    scraper.export_all()
    
    print("\n🎉 Done! Check the 'output' folder for results.")


if __name__ == "__main__":
    main()
