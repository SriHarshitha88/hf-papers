from crewai.tools import BaseTool
from langchain_community.llms import OpenAI
from typing import Dict
import os

class EnhancedSummarizerTool(BaseTool):
    name: str = "Enhanced Research Summarizer"
    description: str = "Creates structured summaries optimized for ArXiv papers"
    
    def _run(self, paper: Dict) -> Dict:
        """Generate enhanced summary with category-specific analysis"""
        
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
        
        try:
            llm = OpenAI(temperature=0)
            response = llm.predict(prompt)
            
            # Parse the response into a structured format
            summary = {
                'key_contributions': [],
                'methodology': '',
                'significance': '',
                'technical_summary': '',
                'practical_applications': '',
                'limitations': '',
                'category': category,
                'difficulty_level': 'Intermediate',
                'keywords': []
            }
            
            # TODO: Implement proper response parsing
            # This is a placeholder for the actual parsing logic
            
            return summary
        except Exception as e:
            return f"Error generating summary: {str(e)}" 