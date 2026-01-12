# Adapting the Scraper for Other BetterDocs Sites

This guide will help you adapt the scraper for other BetterDocs-powered documentation sites.

## Quick Test

Before making changes, try running the scraper on your target site:

```python
scraper = KnowledgeBaseScraper(base_url="https://your-site.com")
scraper.scrape_all()
```

If it works, great! If not, follow this guide.

## Step 1: Update the Base URL

In `scraper.py`, change the base URL:

```python
# Change this line in __init__
self.base_url = "https://your-target-site.com"
self.docs_url = f"{base_url}/docs/"  # Or your custom docs path
```

## Step 2: Check URL Patterns

BetterDocs typically uses these patterns:
- Main page: `/docs/`
- Categories: `/docs-category/{slug}/`
- Articles: `/docs/{slug}/`

If your site uses different patterns, update these methods:

### In `extract_categories()`:
```python
# Find category links - adjust the href pattern
category_links = soup.find_all('a', href=lambda x: x and '/docs-category/' in x)
# Change '/docs-category/' to match your site's pattern
```

### In `extract_articles_from_category()`:
```python
# Find article links - adjust the href pattern
article_links = soup.find_all('a', href=lambda x: x and '/docs/' in x and '/docs-category/' not in x)
# Adjust patterns as needed
```

## Step 3: Inspect Content Structure

Visit an article page on your target site and inspect the HTML to find where the content is located.

### Common BetterDocs Content Containers:
- `<div class="betterdocs-content">`
- `<article>`
- `<div class="entry-content">`
- `<main>`

### Update `extract_article_content()`:

```python
# Find the main content container
content_div = (
    soup.find('div', class_='betterdocs-content') or  # Standard BetterDocs
    soup.find('article') or                            # Generic article tag
    soup.find('div', class_='entry-content') or        # WordPress standard
    soup.find('main') or                               # HTML5 main tag
    soup.find('div', class_='your-custom-class')       # Add your custom class
)
```

## Step 4: Test Category Discovery

Run this test to see if categories are being found:

```python
scraper = KnowledgeBaseScraper(base_url="https://your-site.com")
categories = scraper.extract_categories()
print(f"Found {len(categories)} categories:")
for cat in categories:
    print(f"  - {cat['name']}: {cat['url']}")
```

If no categories are found, inspect the main docs page and look for:
- Links to category pages
- CSS classes or IDs used for category cards
- Any JavaScript-based navigation

## Step 5: Test Article Extraction

Test article extraction from a single category:

```python
scraper = KnowledgeBaseScraper(base_url="https://your-site.com")
articles = scraper.extract_articles_from_category("https://your-site.com/docs-category/test/")
print(f"Found {len(articles)} articles")
for article_url in articles:
    print(f"  - {article_url}")
```

## Step 6: Test Content Extraction

Test content extraction from a single article:

```python
scraper = KnowledgeBaseScraper(base_url="https://your-site.com")
article = scraper.extract_article_content(
    "https://your-site.com/docs/test-article/",
    "Test Category"
)
print(f"Title: {article['title']}")
print(f"Content length: {len(article['content'])} characters")
print(f"First 200 chars: {article['content'][:200]}")
```

## Common Issues and Solutions

### Issue 1: No Categories Found

**Cause**: Different HTML structure or JavaScript-based navigation

**Solution**: Inspect the page source and update the selector:
```python
# Try different selectors
category_links = soup.find_all('a', class_='category-card')
# or
category_links = soup.select('.betterdocs-categories a')
# or
category_links = soup.find_all('a', attrs={'data-category': True})
```

### Issue 2: No Articles Found

**Cause**: Different article link structure

**Solution**: Look for article links in the category page:
```python
# Try finding links within a specific container
article_container = soup.find('div', class_='articles-list')
if article_container:
    article_links = article_container.find_all('a')
```

### Issue 3: Content Not Extracted

**Cause**: Different content container

**Solution**: Inspect the article page and find the main content div:
```python
# Add debugging to see what's available
print("Available classes:", [div.get('class') for div in soup.find_all('div')])

# Then update the selector
content_div = soup.find('div', class_='your-actual-content-class')
```

### Issue 4: Getting Duplicate Articles

**Cause**: Multiple links to the same article (sidebar, footer, etc.)

**Solution**: The scraper already uses `seen_urls` set to avoid duplicates, but you can add more filtering:
```python
# Filter out navigation links
article_links = [
    link for link in soup.find_all('a', href=lambda x: x and '/docs/' in x)
    if 'nav' not in link.get('class', []) and 'footer' not in link.get('class', [])
]
```

## Advanced Customization

### Custom Rate Limiting

Adjust delays based on the site's capacity:
```python
# In scrape_all() method
time.sleep(2)  # Increase delay between categories
time.sleep(1)  # Increase delay between articles
```

### Custom User Agent

Some sites may block the default user agent:
```python
# In __init__ method
self.session.headers.update({
    'User-Agent': 'YourCustomUserAgent/1.0'
})
```

### Authentication

If the site requires login:
```python
# Add authentication in __init__
self.session.auth = ('username', 'password')
# or
self.session.cookies.set('session_token', 'your_token')
```

## Testing Checklist

- [ ] Categories are discovered correctly
- [ ] Article URLs are extracted from categories
- [ ] Article titles are correct
- [ ] Article content is complete (not truncated)
- [ ] No duplicate articles
- [ ] All three export formats work
- [ ] Rate limiting is appropriate

## Example: Adapting for a Custom Site

Here's a complete example of adapting for a hypothetical site:

```python
class CustomSiteScraper(KnowledgeBaseScraper):
    def __init__(self):
        super().__init__(base_url="https://custom-site.com")
        self.docs_url = f"{self.base_url}/documentation/"  # Custom path
    
    def extract_categories(self):
        """Override for custom category structure"""
        html = self.get_page(self.docs_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        categories = []
        
        # Custom selector for this site
        category_cards = soup.find_all('div', class_='doc-category-card')
        
        for card in category_cards:
            link = card.find('a')
            if link:
                categories.append({
                    'name': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href')),
                    'articles': []
                })
        
        return categories

# Use the custom scraper
scraper = CustomSiteScraper()
scraper.scrape_all()
```

## Need Help?

If you're having trouble adapting the scraper:

1. Share the target site URL
2. Describe what's not working
3. Include any error messages
4. Show the HTML structure of the problematic elements

Open an issue on GitHub with this information, and I'll help you adapt it!
