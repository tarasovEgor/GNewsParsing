import pandas as pd
import requests
from newspaper import Article
from datetime import datetime
import time
import re

# GNews API key (insert your key here)
API_KEY = ''

LANG = 'ru'
MAX_ARTICLES_PER_QUERY = 10

EXCEL_PATH = 'src/data/companies.xlsx'
OUTPUT_CSV = 'gnews_parsed_articles.csv'

# Search query patterns using company name and year
QUERY_PATTERNS = [
    '{} social activity {}',
    '{} social projects {}',
    '{} environmental activity {}',
    '{} environmental projects {}',
    '{} corporate changes {}'
]

# Company official domains to filter out articles from these websites
COMPANY_DOMAINS = [
    'gazprom.ru', 'lukoil.ru', 'rosneft.ru', 'sberbank.ru',
    'norilsknickel.ru', 'tatneft.ru', 'novatek.ru' 
]

# Function to check if an article URL is from a company domain
def is_company_domain(url):
    return any(domain in url for domain in COMPANY_DOMAINS)

# List to collect results
results = []

df = pd.read_excel(EXCEL_PATH, sheet_name='использовать для парсера')

# Loop through each company and year
for _, row in df.iterrows():
    company = row['company']
    year = row['Year']

    for pattern in QUERY_PATTERNS:
        query = pattern.format(company, year)
        print(f"🔍 Searching for query: {query}")
        
        url = f'https://gnews.io/api/v4/search?q={query}&lang={LANG}&token={API_KEY}'

        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"⚠️ Error: {response.status_code} for query: {query}")
                continue

            data = response.json()
            for article in data.get('articles', []):
                article_url = article['url']
                if is_company_domain(article_url):
                    print(f"Skipped company domain article: {article_url}")
                    continue

                try:
                    # Download and parse full article text
                    article_obj = Article(article_url)
                    article_obj.download()
                    article_obj.parse()
                    full_text = article_obj.text
                except Exception as e:
                    print(f"Error parsing article text: {e}")
                    full_text = None

                # Parse and format publication date
                pubdate = article.get('publishedAt')
                try:
                    pubdate_fmt = datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%SZ").strftime("%d-%m-%Y %H:%M")
                except:
                    pubdate_fmt = pubdate

                # Append article data to the results
                results.append({
                    'link': article_url,
                    'pubdate': pubdate_fmt,
                    'article_body': full_text,
                    'title': article.get('title'),
                    'query': query,
                    'label': company,
                    'source': article.get('source', {}).get('name')
                })
            time.sleep(1)

        except Exception as e:
            print(f"Error during API request: {e}")

df_result = pd.DataFrame(results)
df_result.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved {len(results)} results to {OUTPUT_CSV}")