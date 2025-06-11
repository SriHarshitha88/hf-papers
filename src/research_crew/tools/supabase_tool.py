from crewai.tools import BaseTool
from supabase import create_client, Client
import os
from typing import Dict, List
from pydantic import PrivateAttr
from dotenv import load_dotenv
import logging

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
            logging.info(f"Received {len(papers_data)} papers for storage")
            
            # Validate and clean data before insertion
            cleaned_papers = []
            for i, paper in enumerate(papers_data):
                logging.info(f"Processing paper {i+1}: {paper.get('title', 'No title')}")
                cleaned_paper = self._clean_paper_data(paper)
                if cleaned_paper:
                    cleaned_papers.append(cleaned_paper)
                    logging.info(f"Successfully cleaned paper {i+1}")
                else:
                    logging.warning(f"Failed to clean paper {i+1}")
            
            if not cleaned_papers:
                logging.error("No valid papers after cleaning")
                return "No valid papers to store"
            
            logging.info(f"Attempting to store {len(cleaned_papers)} cleaned papers")
            
            # Insert papers into database
            result = self._supabase.table('research_papers').insert(cleaned_papers).execute()
            logging.info(f"Successfully stored {len(cleaned_papers)} papers")
            return f"Successfully stored {len(cleaned_papers)} papers"
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error storing papers: {error_msg}")
            return f"Error storing papers: {error_msg}"
    
    def _clean_paper_data(self, paper: Dict) -> Dict:
        """Clean and validate paper data before storage"""
        # Map of required fields and their types
        required_fields = {
            'title': str,
            'abstract': str,
            'authors': list,
            'primary_category': str,
            'technical_summary': str
        }
        
        cleaned_paper = {}
        
        # Log the incoming paper data
        logging.info(f"Cleaning paper: {paper.get('title', 'No title')}")
        
        # Ensure required fields exist and have correct types
        for field, field_type in required_fields.items():
            value = paper.get(field)
            if value is None:
                logging.warning(f"Missing required field: {field}")
                if field_type == list:
                    cleaned_paper[field] = []
                elif field_type == str:
                    cleaned_paper[field] = ''
                else:
                    cleaned_paper[field] = None
            else:
                cleaned_paper[field] = value
                logging.info(f"Field {field} validated")
        
        # Add optional fields if they exist
        optional_fields = [
            'key_contributions',
            'methodology',
            'significance',
            'practical_applications',
            'limitations',
            'difficulty_level'
        ]
        
        for field in optional_fields:
            if field in paper:
                cleaned_paper[field] = paper[field]
                logging.info(f"Added optional field: {field}")
        
        # Validate the cleaned paper
        if not cleaned_paper.get('title') or not cleaned_paper.get('abstract'):
            logging.error("Paper missing essential fields after cleaning")
            return None
            
        return cleaned_paper
            
    def check_duplicate(self, paper_url: str) -> bool:
        """Check if a paper already exists in the database"""
        try:
            result = self._supabase.table('research_papers').select('id').eq('paper_url', paper_url).execute()
            return len(result.data) > 0
        except Exception as e:
            logging.error(f"Error checking duplicate: {str(e)}")
            return False 