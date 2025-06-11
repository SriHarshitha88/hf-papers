from crewai.tools import BaseTool
from langchain_openai import OpenAI
from typing import Dict, List
import os
import json

class EnhancedSummarizerTool(BaseTool):
    name: str = "Enhanced Research Summarizer"
    description: str = "Creates structured summaries optimized for ArXiv papers"
    
    def _run(self, papers: List[Dict]) -> List[Dict]:
        """Batch process: Generate enhanced summaries for a list of papers"""
        results = []
        for paper in papers:
            try:
                summary = self._summarize_paper(paper)
                results.append(summary)
            except Exception as e:
                print(f"Error summarizing paper: {str(e)}")
                results.append(paper)  # Append original if summarization fails
        return results

    def _summarize_paper(self, paper: Dict) -> Dict:
        """Summarize a single paper"""
        category = paper.get('primary_category', 'Machine Learning')
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        # Category-specific prompts
        category_prompts = {
            'Computer Vision': "Focus on datasets used, model architecture, and visual tasks addressed.",
            'Natural Language Processing': "Highlight language tasks, model types, and performance metrics.",
            'Machine Learning': "Emphasize methodology, algorithms, and theoretical contributions.",
            'Reinforcement Learning': "Focus on environment, reward structure, and learning algorithms.",
            'Deep Learning': "Highlight architecture innovations, training techniques, and applications."
        }
        
        specific_prompt = category_prompts.get(category, "Focus on methodology and key contributions.")
        
        # This would connect to your LLM
        prompt = f"""
        Analyze this {category} research paper and create a structured summary:

        Title: {title}
        Abstract: {abstract}

        {specific_prompt}

        Provide analysis in this JSON format:
        {{
            "key_contributions": ["3-4 main contributions"],
            "methodology": "Primary research approach and methods used",
            "significance": "Why this research matters and its potential impact",
            "technical_summary": "2-sentence technical overview for experts",
            "practical_applications": "Real-world applications of this research",
            "limitations": "Key limitations or areas for future work",
            "category": "{category}",
            "difficulty_level": "Beginner/Intermediate/Advanced",
            "keywords": ["5-6 relevant keywords"]
        }}
        """
        
        llm = OpenAI(temperature=0)
        response = llm.invoke(prompt)

        # Try to parse as JSON
        try:
            summary = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: use full response as technical_summary
            summary = {
                'key_contributions': [],
                'methodology': '',
                'significance': '',
                'technical_summary': response,
                'practical_applications': '',
                'limitations': '',
                'category': category,
                'difficulty_level': 'Intermediate',
                'keywords': []
            }
        
        # Ensure all required fields exist
        required_fields = [
            'key_contributions', 'methodology', 'significance',
            'technical_summary', 'practical_applications', 'limitations',
            'category', 'difficulty_level', 'keywords'
        ]
        for field in required_fields:
            if field not in summary:
                summary[field] = [] if field in ['key_contributions', 'keywords'] else ''
        
        # Merge with original paper data
        paper.update(summary)
        return paper
