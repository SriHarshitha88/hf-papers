from crewai.tools import BaseTool
import requests
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Dict, Optional
import feedparser
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pydantic import Field

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
                        'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                        'arxiv_url': f"https://arxiv.org/abs/{arxiv_id}",
                        'published': published,
                        'categories': categories_list,
                        'primary_category': primary_category,
                        'source': 'arxiv',
                        'fetched_at': datetime.now().isoformat()
                    }
                    
                    papers.append(paper_data)
                    
                except Exception as e:
                    print(f"Error parsing paper: {e}")
                    continue
            
            return papers[:limit]  # Return exactly the requested number
            
        except Exception as e:
            return f"Error fetching from ArXiv: {str(e)}"
    
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
        
        try:
            feed = feedparser.parse(rss_url)
            papers = []
            
            for entry in feed.entries[:limit]:
                paper = {
                    'title': entry.title,
                    'abstract': entry.get('summary', ''),
                    'link': entry.link,
                    'published': entry.get('published', ''),
                    'authors': [author.get('name', '') for author in entry.get('authors', [])],
                    'primary_category': 'Trending Research',
                    'source': 'huggingface_trending',
                    'fetched_at': datetime.now().isoformat()
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            return f"Error fetching HF trending: {str(e)}"

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
        - 80% from ArXiv (most recent, high quality)
        - 20% from HuggingFace trending (curated highlights)
        """
        
        arxiv_count = max(1, int(total_limit * 0.8))  # At least 1 from ArXiv
        hf_count = total_limit - arxiv_count
        
        all_papers = []
        
        # Fetch from ArXiv
        try:
            arxiv_papers = self.arxiv_tool._run(limit=arxiv_count, days_back=7)
            if isinstance(arxiv_papers, list):
                all_papers.extend(arxiv_papers)
        except Exception as e:
            print(f"ArXiv fetch failed: {e}")
        
        # Supplement with HuggingFace trending
        try:
            hf_papers = self.hf_tool._run(limit=hf_count)
            if isinstance(hf_papers, list):
                all_papers.extend(hf_papers)
        except Exception as e:
            print(f"HF fetch failed: {e}")
        
        # Remove duplicates based on title similarity
        unique_papers = self._deduplicate_papers(all_papers)
        
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