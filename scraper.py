#!/usr/bin/env python3
"""
Knowledge Base Web Scraper
Scrapes all content from BetterDocs-powered documentation websites
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
        
        # Find all category cards - BetterDocs uses specific structure
        category_cards = soup.find_all('article', class_='betterdocs-single-category-wrapper')
        
        if not category_cards:
            # Fallback: try finding category links directly
            category_links = soup.find_all('a', href=lambda x: x and '/docs-category/' in x)
            seen_urls = set()
            for link in category_links:
                url = urljoin(self.base_url, link.get('href'))
                if url not in seen_urls:
                    seen_urls.add(url)
                    category_name = link.get_text(strip=True) or url.split('/')[-2]
                    if category_name and category_name.lower() not in ['explore more', 'read more', 'view all']:
                        categories.append({
                            'name': category_name,
                            'url': url,
                            'articles': []
                        })
        else:
            # Extract from category cards (preferred method)
            seen_urls = set()
            for card in category_cards:
                # Get the category title from the title element
                title_elem = card.find(class_='betterdocs-category-title')
                category_name = title_elem.get_text(strip=True) if title_elem else None
                
                # Get the category URL from the link
                link = card.find('a', href=lambda x: x and '/docs-category/' in x)
                
                if link and category_name:
                    url = urljoin(self.base_url, link.get('href'))
                    if url not in seen_urls:
                        seen_urls.add(url)
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
        
        # Get the page title to know which category we're on
        h1 = soup.find('h1')
        page_title = h1.get_text(strip=True) if h1 else ""
        
        # Find all category wrappers
        all_wrappers = soup.find_all(class_='betterdocs-single-category-wrapper')
        
        if all_wrappers:
            # Find the wrapper that matches the current page
            # The correct wrapper will have a title matching the H1 or be marked as active/show
            target_wrapper = None
            
            for wrapper in all_wrappers:
                # Check if this wrapper has the active or show class
                wrapper_classes = wrapper.get('class', [])
                if 'active' in wrapper_classes or 'show' in wrapper_classes:
                    target_wrapper = wrapper
                    break
                
                # Fallback: match by title
                title_elem = wrapper.find(class_='betterdocs-category-title')
                if title_elem:
                    wrapper_title = title_elem.get_text(strip=True)
                    if wrapper_title and wrapper_title in page_title:
                        target_wrapper = wrapper
                        break
            
            if target_wrapper:
                # Get articles from this specific wrapper
                article_list = target_wrapper.find('ul', class_='betterdocs-articles-list')
                if article_list:
                    article_links = article_list.find_all('a', href=lambda x: x and '/docs/' in x)
                else:
                    article_links = []
            else:
                # If no match found, use the first list (fallback)
                article_list = soup.find('ul', class_='betterdocs-articles-list')
                if article_list:
                    article_links = article_list.find_all('a', href=lambda x: x and '/docs/' in x)
                else:
                    article_links = []
        else:
            # No wrappers found, try direct article list
            article_list = soup.find('ul', class_='betterdocs-articles-list')
            if article_list:
                article_links = article_list.find_all('a', href=lambda x: x and '/docs/' in x)
            else:
                # Last resort
                article_links = soup.find_all('a', href=lambda x: x and '/docs/' in x and '/docs-category/' not in x)
        
        seen_urls = set()
        for link in article_links:
            url = urljoin(self.base_url, link.get('href'))
            # Avoid duplicates and the main docs page
            if url not in seen_urls and url != self.docs_url and '/docs-category/' not in url:
                seen_urls.add(url)
                articles.append(url)
        
        return articles
    
    def extract_article_content(self, article_url, parent_category_name):
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
            'parent_category': parent_category_name,
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
    
    def export_json(self, output_dir="output", include_urls=False):
        """Export data as JSON"""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / "knowledge_base.json"
        
        # Create a clean version without HTML
        clean_data = {
            "categories": []
        }
        
        # Optionally include base_url
        if include_urls:
            clean_data["base_url"] = self.data["base_url"]
        
        for category in self.data['categories']:
            clean_category = {
                "name": category['name'],
                "articles": []
            }
            
            # Optionally include category URL
            if include_urls:
                clean_category["url"] = category['url']
            
            for article in category['articles']:
                article_data = {
                    'title': article['title'],
                    'parent_category': article['parent_category'],
                    'content': article['content']
                }
                
                # Optionally include article URL
                if include_urls:
                    article_data['url'] = article['url']
                
                clean_category['articles'].append(article_data)
            clean_data['categories'].append(clean_category)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON exported to: {filepath}")
    
    def export_markdown(self, output_dir="output", include_urls=False):
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
                if include_urls:
                    md_content = f"""# {article['title']}

**Parent Category:** {article['parent_category']}  
**URL:** {article['url']}

---

{article['content']}
"""
                else:
                    md_content = f"""# {article['title']}

**Parent Category:** {article['parent_category']}

---

{article['content']}
"""
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
        
        print(f"💾 Markdown files exported to: {base_path}")
    
    def export_csv(self, output_dir="output", include_urls=False):
        """Export data as CSV"""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = Path(output_dir) / "knowledge_base.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row based on include_urls setting
            if include_urls:
                writer.writerow(['Category', 'Title', 'URL', 'Content'])
            else:
                writer.writerow(['Category', 'Title', 'Content'])
            
            for category in self.data['categories']:
                for article in category['articles']:
                    if include_urls:
                        writer.writerow([
                            article['parent_category'],
                            article['title'],
                            article['url'],
                            article['content']
                        ])
                    else:
                        writer.writerow([
                            article['parent_category'],
                            article['title'],
                            article['content']
                        ])
        
        print(f"💾 CSV exported to: {filepath}")
    
    def export_all(self, output_dir="output", include_urls=False):
        """Export in all formats"""
        print(f"\n📦 Exporting data...\n")
        self.export_json(output_dir, include_urls=include_urls)
        self.export_markdown(output_dir, include_urls=include_urls)
        self.export_csv(output_dir, include_urls=include_urls)
        print(f"\n✅ All exports complete!")


def main():
    # CONFIGURE YOUR SITE HERE
    # Replace with your BetterDocs-powered documentation site URL
    scraper = KnowledgeBaseScraper(base_url="https://your-docs-site.com")
    
    # Scrape all content
    scraper.scrape_all()
    
    # Export in all formats (URLs will be optional)
    scraper.export_all()
    
    print("\n🎉 Done! Check the 'output' folder for results.")


if __name__ == "__main__":
    main()
