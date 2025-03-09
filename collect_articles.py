#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from heapq import nlargest
from datetime import datetime
import json
import frontmatter
import os
import random
import time
from urllib.parse import urljoin

try:
    nltk.download(['stopwords', 'punkt'], quiet=True, download_dir='d:\\zhanhui\\app\\02-blog\\my-blog\\nltk_data')
except Exception as e:
    print(f"Error downloading NLTK data: {e}\nPlease ensure you have internet connectivity and sufficient disk space.")
    nltk.data.path.append('d:/zhanhui/app/02-blog/my-blog/nltk_data')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print('Using backup stopwords list')
        stopwords.words = lambda _: []

# New clinical trial metadata extractor
# Updated content extraction

def get_article_content(url):
    try:
        headers = {
    'Authority': 'synapse.patsnap.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Sec-Ch-Ua': '"Chromium";v="125", "Google Chrome";v="125", "Not.A/Brand";v="24"',
    'Cookie': 'geo=US;',
    'X-Requested-With': 'XMLHttpRequest',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://synapse.patsnap.com/blog',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        }
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10)
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching article from {url}: {e}\nCheck your network connection and the website's availability.")
        return None

def summarize_with_deepseek(text):
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'deepseek-r1:7b',
                'prompt': f'详细总结文章内容，不要以第三人称视角，重点突出关键创新点和临床意义，字数不限，输出内容不体现思考过程，直接输出结果：\n\n{text}',
                'stream': False,
                'options': {'temperature': 0.5}
            }
        )
        response.raise_for_status()
        return response.json()['response'].strip()
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return None

def summarize_article(content):
    try:
        if content is None:
            return None
        soup = BeautifulSoup(content, 'html.parser')
        article_body = soup.find('article') or soup.find('div', class_='content-body')
        # Replace NLTK summarization with DeepSeek
        if not article_body:
            print(f'内容容器未找到，页面结构可能已变更，保存调试文件')
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
        raw_text = ' '.join([p.get_text().strip() for p in article_body.find_all(['p', 'div', 'section']) if p.get_text().strip()]) if article_body else ''
        chinese_summary = summarize_with_deepseek(raw_text[:2000])  # Truncate for model context
        return chinese_summary
    except Exception as e:
        print(f'Error generating summary: {e}')
        return None

url = 'https://synapse.patsnap.com/blog/posts'

headers = {
    'Authority': 'synapse.patsnap.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://synapse.patsnap.com/blog',
    'Cookie': 'session_cookie=1; geo=US;'
}

def collect_and_summarize_articles():
    print("\n=== Starting article collection ===\n")
    try:
        time.sleep(random.uniform(1, 3))
        try:
            response = requests.get(url, headers=headers, cookies={'session_cookie': '1'}, timeout=10)
            try:
                with open('debug_listing.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
            except Exception as e:
                print(f'Failed to save debug listing: {e}')
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                print('触发反爬机制，尝试使用备用头信息')
                headers.update({'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'})
                headers.update({'Accept-Language': 'en-US,en;q=0.9', 'DNT': '1', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate'})
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            else:
                raise
        response.raise_for_status()
        if not response:
            print('Empty response received')
            return
        with open('debug_listing.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Updated selector for current article links
        article_links = [a['href'] for a in soup.select('div.post-list-item a.post-link')][:10]  # Target blog listing container links
        if not article_links:
            print('No articles found! Printing page structure:')
            print(soup.prettify()[:2000])
        print(f"Found {len(article_links)} articles")
        for link in article_links:
            full_link = urljoin(url, link)
            if not full_link.startswith(('http://', 'https://')):
                print(f"Invalid URL format: {full_link}")
                continue
            content = get_article_content(full_link)
            summary = summarize_article(content)
            if summary is not None:
                print(f"Summary: {summary}")
                print(f"Article Link: {full_link}")
                print("\n")
                # Bug fix: Correct the call to summarize_article and ensure post is correctly assigned
                # Create post using frontmatter's proper API
                post = frontmatter.loads('')
                post['title'] = 'Article Summary'
                post['date'] = datetime.now().isoformat()
                post['link'] = full_link
                
                post.content = f"{summary or '摘要生成失败'}\n\n原文链接: {full_link}"
                if not post.content.strip(): 
                    print(f"Skipping empty post for {full_link}")
                    continue
                
            # Always save regardless of summary status
            os.makedirs('content/posts', exist_ok=True)
            filename = f"content/posts/{datetime.now().strftime('%Y%m%d')}_{random.getrandbits(32)}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                print(f"Saving article to {filename}")
                f.write(frontmatter.dumps(post))
    except requests.RequestException as e:
        print(f"Error fetching article list from {url}: {e}\nThe website may have changed its structure or implemented anti-scraping measures.")
    except Exception as e:
        print(f"Unexpected error occurred: {str(e)}\nPlease check the debug files for more information.")
        # Bug fix: Remove the incorrect reference to metadata
        # print(f"Generated metadata:\n{json.dumps(metadata, indent=2)}")
        
if __name__ == '__main__':
    collect_and_summarize_articles()