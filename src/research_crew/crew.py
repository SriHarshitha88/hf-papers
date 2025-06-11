from crewai import Agent, Task, Crew, Process
from langchain_community.llms import OpenAI

from tools.arxiv_tools import SmartResearchFetcher
from tools.summarizer_tool import EnhancedSummarizerTool
from tools.supabase_tool import SupabaseTool

import yaml
import os

class ResearchCrew:
    def __init__(self):
        self.load_configs()
        self.setup_tools()
        self.setup_agents()
        self.setup_tasks()
        
    def load_configs(self):
        with open('src/research_crew/config/agents.yaml', 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open('src/research_crew/config/tasks.yaml', 'r') as f:
            self.tasks_config = yaml.safe_load(f)
    
    def setup_tools(self):
        self.research_fetcher = SmartResearchFetcher()
        self.summarizer_tool = EnhancedSummarizerTool()
        self.supabase_tool = SupabaseTool()
    
    def setup_agents(self):
        self.research_fetcher_agent = Agent(
            config=self.agents_config['rss_fetcher'],
            tools=[self.research_fetcher],
            verbose=True
        )
        
        self.research_summarizer = Agent(
            config=self.agents_config['research_summarizer'],
            tools=[self.summarizer_tool],
            verbose=True
        )
        
        self.database_manager = Agent(
            config=self.agents_config['database_manager'],
            tools=[self.supabase_tool],
            verbose=True
        )
    
    def setup_tasks(self):
        self.fetch_task = Task(
            config=self.tasks_config['fetch_papers'],
            agent=self.research_fetcher_agent
        )
        
        self.summarize_task = Task(
            config=self.tasks_config['summarize_papers'],
            agent=self.research_summarizer,
            context=[self.fetch_task]
        )
        
        self.store_task = Task(
            config=self.tasks_config['store_papers'],
            agent=self.database_manager,
            context=[self.fetch_task, self.summarize_task]
        )
    
    def run(self):
        crew = Crew(
            agents=[self.research_fetcher_agent, self.research_summarizer, self.database_manager],
            tasks=[self.fetch_task, self.summarize_task, self.store_task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew.kickoff() 