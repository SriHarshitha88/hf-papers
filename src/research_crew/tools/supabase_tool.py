from crewai.tools import BaseTool
from supabase import create_client, Client
import os
from typing import Dict, List
from pydantic import PrivateAttr
from dotenv import load_dotenv

load_dotenv()

class SupabaseTool(BaseTool):
    name: str = "Supabase Manager"
    description: str = "Manages research papers storage in Supabase"
    
    _supabase: Client = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
    
    def _run(self, papers_data: List[Dict]) -> str:
        """Store papers and summaries in Supabase"""
        
        try:
            # Validate and clean data before insertion
            cleaned_papers = []
            for paper in papers_data:
                cleaned_paper = self._clean_paper_data(paper)
                if cleaned_paper:
                    cleaned_papers.append(cleaned_paper)
            
            if not cleaned_papers:
                return "No valid papers to store"
            
            # Insert papers into database
            result = self._supabase.table('research_papers').insert(cleaned_papers).execute()
            return f"Successfully stored {len(cleaned_papers)} papers"
        except Exception as e:
            print(f"Error storing papers: {str(e)}")
            return f"Error storing papers: {str(e)}"
    
    def _clean_paper_data(self, paper: Dict) -> Dict:
        """Clean and validate paper data before storage"""
        required_fields = {
            'title': str,
            'abstract': str,
            'authors': list,
            'category': str,
            'technical_summary': str
        }
        
        cleaned_paper = {}
        
        # Ensure required fields exist and have correct types
        for field, field_type in required_fields.items():
            value = paper.get(field)
            if value is None:
                if field_type == list:
                    cleaned_paper[field] = []
                elif field_type == str:
                    cleaned_paper[field] = ''
                else:
                    cleaned_paper[field] = None
            else:
                cleaned_paper[field] = value
        
        # Add optional fields if they exist
        optional_fields = [
            'key_contributions', 'methodology', 'significance',
            'practical_applications', 'limitations', 'difficulty_level',
            'keywords', 'paper_url', 'arxiv_id', 'published_date'
        ]
        
        
        for field in optional_fields:
            if field in paper:
                cleaned_paper[field] = paper[field]
        
        return cleaned_paper
            
    def check_duplicate(self, paper_url: str) -> bool:
        """Check if a paper already exists in the database"""
        try:
            result = self._supabase.table('research_papers').select('id').eq('paper_url', paper_url).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking duplicate: {str(e)}")
            return False 