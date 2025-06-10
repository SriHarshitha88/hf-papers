from crew import ResearchCrew
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    research_crew = ResearchCrew()
    result = research_crew.run()
    
    print("Research Papers Processing Complete!")
    print(result)

if __name__ == "__main__":
    main() 