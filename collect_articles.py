import requests
from bs4 import BeautifulSoup
import frontmatter
import pandas as pd
import os
from urllib.parse import urlparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class ArticleCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    def clean_content(self, soup):
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe']):
            element.decompose()
        
        for p in soup.find_all('p'):
            p.string = ' '.join(p.get_text().split())
        
        return str(soup)

    def scrape_article(self, url):
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            main_content = soup.find('article') or \
                           soup.find('div', class_=lambda x: x and 'content' in x) or \
                           soup.find('div', id=lambda x: x and 'content' in x)
            
            if not main_content:
                return None
            
            return {
                'title': (soup.title.string.strip() if soup.title else urlparse(url).path),
                'content': self.clean_content(main_content),
                'source_url': url,
                'tags': list(set([a.get_text().strip() for a in soup.find_all('a', class_=lambda x: x and 'tag' in x)]))
            }
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return None

    def save_as_markdown(self, article, output_dir='content/posts'):
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            safe_title = ''.join(c if c.isalnum() else '_' for c in article['title'])[:50]
            filename = f"{datetime.now().strftime('%Y%m%d')}_{safe_title}.md"
            
            post = frontmatter.Post(
                article['content'],
                title=article['title'],
                date=datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
                categories=article['tags'],
                draft=False,
                source_url=article['source_url']
            )
            
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(f'---\n{frontmatter.dumps(post.metadata)}\n---\n\n{post.content}')
            
            logging.info(f"Successfully saved: {filename}")
            
        except Exception as e:
            logging.error(f"Failed to save article: {str(e)}")

if __name__ == '__main__':
    collector = ArticleCollector()
    
    df = pd.read_excel('websites.xlsx')
print('Excel columns:', df.columns.tolist())
try:
    urls = df['URL'].tolist()
except KeyError:
    raise ValueError("Excel file must contain 'URL' column. Current columns: " + str(df.columns.tolist()))
    
    for index, url in enumerate(urls):
        logging.info(f"Processing ({index+1}/{len(urls)}): {url}")
        if article := collector.scrape_article(url):
            collector.save_as_markdown(article)