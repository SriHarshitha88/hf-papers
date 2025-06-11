from crewai.tools import BaseTool
import requests
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Dict, Optional
import feedparser
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pydantic import Field
import logging

class OptimizedArXivTool(BaseTool):
    name: str = "ArXiv Research Fetcher"
    description: str = "Fetches latest AI/ML research papers from ArXiv"
    
    def _run(self, limit: int = 5, days_back: int = 7) -> List[Dict]:
        """
        Fetch recent AI/ML papers from ArXiv
        
        Args:
            limit: Number of papers to fetch
            days_back: How many days back to search
        """
        logging.info(f"Fetching {limit} papers from ArXiv for the last {days_back} days")
        
        # ArXiv categories for AI/ML research
        categories = [
            'cs.AI',    # Artificial Intelligence
            'cs.LG',    # Machine Learning  
            'cs.CL',    # Computation and Language (NLP)
            'cs.CV',    # Computer Vision
            'cs.NE',    # Neural and Evolutionary Computing
            'stat.ML'   # Machine Learning (Statistics)
        ]
        
        # Build search query
        cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
        
        # Date filter (last week)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_filter = f'submittedDate:[{start_date.strftime("%Y%m%d")}* TO {end_date.strftime("%Y%m%d")}*]'
        
        search_query = f'({cat_query}) AND {date_filter}'
        logging.info(f"Search query: {search_query}")
        
        # ArXiv API parameters
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': limit * 2,  # Get extra to filter out irrelevant ones
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # Build URL
        base_url = "http://export.arxiv.org/api/query?"
        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        url = base_url + query_string
        
        try:
            logging.info(f"Making request to ArXiv API: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            papers = []
            
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', namespace)[:limit]:
                try:
                    # Extract basic info
                    title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
                    summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
                    
                    # Authors
                    authors = []
                    for author in entry.findall('atom:author', namespace):
                        name = author.find('atom:name', namespace).text
                        authors.append(name)
                    
                    # ArXiv ID and links
                    entry_id = entry.find('atom:id', namespace).text
                    arxiv_id = entry_id.split('/')[-1]
                    
                    # Published date
                    published = entry.find('atom:published', namespace).text
                    
                    # Categories
                    categories_list = []
                    for category in entry.findall('atom:category', namespace):
                        categories_list.append(category.get('term'))
                    
                    # Determine primary category for classification
                    primary_category = self._classify_paper(categories_list, title, summary)
                    
                    paper_data = {
                        'title': title,
                        'abstract': summary,
                        'authors': authors,
                        'arxiv_id': arxiv_id,
                        'paper_url': f"https://arxiv.org/abs/{arxiv_id}",
                        'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                        'published_date': published,
                        'categories': categories_list,
                        'primary_category': primary_category,
                        'source': 'arxiv',
                        'fetched_at': datetime.now().isoformat()
                    }
                    
                    logging.info(f"Successfully parsed paper: {title}")
                    papers.append(paper_data)
                    
                except Exception as e:
                    logging.error(f"Error parsing paper: {str(e)}")
                    continue
            
            logging.info(f"Successfully fetched {len(papers)} papers from ArXiv")
            return papers[:limit]  # Return exactly the requested number
            
        except Exception as e:
            logging.error(f"Error fetching from ArXiv: {str(e)}")
            return []
    
    def _classify_paper(self, categories: List[str], title: str, abstract: str) -> str:
        """Classify paper into main research area"""
        
        # Classification mapping
        classification_map = {
            'cs.CV': 'Computer Vision',
            'cs.CL': 'Natural Language Processing',
            'cs.LG': 'Machine Learning',
            'cs.AI': 'Artificial Intelligence',
            'cs.NE': 'Neural Computing',
            'stat.ML': 'Statistical ML'
        }
        
        # Check categories first
        for cat in categories:
            if cat in classification_map:
                return classification_map[cat]
        
        # Fallback: keyword-based classification
        text = (title + " " + abstract).lower()
        
        if any(word in text for word in ['vision', 'image', 'visual', 'cnn', 'object detection']):
            return 'Computer Vision'
        elif any(word in text for word in ['nlp', 'language', 'text', 'bert', 'transformer']):
            return 'Natural Language Processing'
        elif any(word in text for word in ['reinforcement', 'rl', 'agent', 'policy']):
            return 'Reinforcement Learning'
        elif any(word in text for word in ['neural', 'deep', 'network', 'cnn', 'rnn']):
            return 'Deep Learning'
        else:
            return 'Machine Learning'

class HuggingFaceSupplementTool(BaseTool):
    name: str = "HuggingFace Supplement"
    description: str = "Gets trending papers from HuggingFace for additional coverage"
    
    def _run(self, limit: int = 3) -> List[Dict]:
        """Get trending papers from HF RSS as supplement"""
        
        rss_url = "https://jamesg.blog/hf-papers.xml"
        logging.info(f"Fetching {limit} papers from HuggingFace RSS feed")
        
        try:
            feed = feedparser.parse(rss_url)
            papers = []
            
            for entry in feed.entries[:limit]:
                try:
                    # Extract and clean the data
                    title = entry.title.strip()
                    abstract = entry.get('summary', '').strip()
                    link = entry.link.strip()
                    
                    # Get authors, default to empty list if none found
                    authors = []
                    if 'authors' in entry:
                        authors = [author.get('name', '').strip() for author in entry.authors if author.get('name')]
                    
                    # Get published date
                    published = entry.get('published', '')
                    
                    paper = {
                        'title': title,
                        'abstract': abstract,
                        'paper_url': link,
                        'published_date': published,
                        'authors': authors,
                        'primary_category': 'Trending Research',
                        'source': 'huggingface_trending',
                        'fetched_at': datetime.now().isoformat(),
                        'technical_summary': abstract[:500] + '...' if len(abstract) > 500 else abstract  # Initial technical summary
                    }
                    
                    logging.info(f"Successfully parsed paper: {title}")
                    papers.append(paper)
                    
                except Exception as e:
                    logging.error(f"Error parsing paper entry: {str(e)}")
                    continue
            
            logging.info(f"Successfully fetched {len(papers)} papers from HuggingFace")
            return papers
            
        except Exception as e:
            logging.error(f"Error fetching HF trending: {str(e)}")
            return []

class SmartResearchFetcher(BaseTool):
    name: str = "Smart Research Fetcher"
    description: str = "Intelligently combines ArXiv and HuggingFace sources"
    arxiv_tool: Optional[OptimizedArXivTool] = Field(default=None)
    hf_tool: Optional[HuggingFaceSupplementTool] = Field(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arxiv_tool = OptimizedArXivTool()
        self.hf_tool = HuggingFaceSupplementTool()
    
    def _run(self, total_limit: int = 5) -> List[Dict]:
        """
        Smart fetching strategy:
        - If total_limit is 0, fetch only from HuggingFace
        - Otherwise, fetch from both sources
        """
        all_papers = []
        
        # Fetch from HuggingFace
        try:
            hf_papers = self.hf_tool._run(limit=total_limit)
            if isinstance(hf_papers, list):
                all_papers.extend(hf_papers)
                logging.info(f"Successfully fetched {len(hf_papers)} papers from HuggingFace")
        except Exception as e:
            logging.error(f"HF fetch failed: {e}")
        
        # Remove duplicates based on title similarity
        unique_papers = self._deduplicate_papers(all_papers)
        
        logging.info(f"Total unique papers after deduplication: {len(unique_papers)}")
        return unique_papers[:total_limit]
    
    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on title similarity"""
        
        unique_papers = []
        seen_titles = []
        
        for paper in papers:
            title = paper.get('title', '').lower()
            
            # Check if similar title already exists
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(None, title, seen_title).ratio()
                if similarity > 0.8:  # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_papers.append(paper)
                seen_titles.append(title)
        
        return unique_papers 