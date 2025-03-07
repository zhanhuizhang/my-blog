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
import random
import time
from urllib.parse import urljoin

try:
    nltk.download(['stopwords', 'punkt'], quiet=True)
except Exception as e:
    print(f"Error downloading NLTK data: {e}")
    nltk.data.path.append('nltk_data')
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.statnews.com/',
    'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Cookie': 'geo=US;',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.statnews.com/category/biotech/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        }
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10)
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None

def summarize_article(content):
    try:
        if content is None:
            return None
        soup = BeautifulSoup(content, 'html.parser')
        article_body = soup.find('div', class_='entry-content')
        text = ' '.join([p.get_text() for p in article_body.find_all('p')])
        
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
        
        freq_dist = FreqDist(words)
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            for word in word_tokenize(sentence.lower()):
                if word in freq_dist:
                    sentence_scores[i] = sentence_scores.get(i, 0) + freq_dist[word]
        
        summary_indices = nlargest(3, sentence_scores, key=sentence_scores.get)
        return ' '.join([sentences[i] for i in sorted(summary_indices)])
    except Exception as e:
        print(f'Error generating summary: {e}')
        return None

url = 'https://www.statnews.com/category/biotech/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.statnews.com/',
    'DNT': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Cookie': 'geo=US;',
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.statnews.com/category/biotech/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive'
}

def collect_and_summarize_articles():
    print("\n=== Starting article collection ===\n")
    try:
        time.sleep(random.uniform(1, 3))
        try:
            response = requests.get(url, headers=headers, cookies={'session_cookie': '1'}, timeout=10)
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                print('触发反爬机制，尝试使用备用头信息')
                headers.update({'Accept-Language': 'zh-CN,zh;q=0.9', 'DNT': '1'})
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            else:
                raise
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Updated selector for current article links
        article_links = [a['href'] for a in soup.select('h3 a')][:10]
        if not article_links:
            print('No articles found! Printing page structure:')
            print(soup.prettify()[:2000])
        print(f"Found {len(article_links)} articles")
        for link in article_links:
            full_link = urljoin(url, link)
            content = get_article_content(full_link)
            summary = summarize_article(content)
            if summary is not None:
                print(f"Summary: {summary}")
                print(f"Article Link: {full_link}")
                print("\n")
                # Bug fix: Correct the call to summarize_article and ensure post is correctly assigned
                post = frontmatter.Post(content='Summary unavailable')
                post['link'] = full_link
                
                if summary is not None:
                    post.content = summary
                
                # Always save regardless of summary status
                filename = f"content/posts/{datetime.now().strftime('%Y%m%d')}_{random.getrandbits(32)}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    print(f"Saving article to {filename}")
                    f.write(frontmatter.dumps(post))
    except requests.RequestException as e:
        print(f"Error fetching article list: {e}")
    except Exception as e:
        print(f"Error: {str(e)}")
        # Bug fix: Remove the incorrect reference to metadata
        # print(f"Generated metadata:\n{json.dumps(metadata, indent=2)}")
        
if __name__ == '__main__':
    collect_and_summarize_articles()