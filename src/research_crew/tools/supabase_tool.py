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
            # Insert papers into database
            result = self._supabase.table('research_papers').insert(papers_data).execute()
            return f"Successfully stored {len(papers_data)} papers"
        except Exception as e:
            return f"Error storing papers: {str(e)}"
            
    def check_duplicate(self, paper_url: str) -> bool:
        """Check if a paper already exists in the database"""
        try:
            result = self._supabase.table('research_papers').select('id').eq('paper_url', paper_url).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking duplicate: {str(e)}")
            return False 