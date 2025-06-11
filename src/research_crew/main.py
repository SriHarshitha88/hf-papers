from crew import ResearchCrew
from dotenv import load_dotenv
import schedule
import time
import logging
import argparse
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('research_pipeline.log'),
            logging.StreamHandler()
        ]
    )

def run_research_pipeline():
    """Execute the research crew pipeline with error handling"""
    try:
        logging.info("Starting research pipeline execution...")
        print(f"Pipeline started at: {datetime.now()}")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize and run the research crew
        research_crew = ResearchCrew()
        result = research_crew.run()
        
        logging.info("Research pipeline completed successfully")
        print("Research Papers Processing Complete!")
        print(f"Result: {result}")
        print(f"Completed at: {datetime.now()}")
        
        return result
        
    except Exception as e:
        logging.error(f"Error during research pipeline execution: {str(e)}")
        print(f"Pipeline failed: {str(e)}")
        raise

def start_scheduler():
    """Start the scheduler for daily execution at 2 AM"""
    setup_logging()
    
    logging.info("Research Pipeline Scheduler started")
    print("Research Pipeline Scheduler started")
    
    # Schedule the task to run daily at 2:00 AM
    schedule.every().day.at("02:00").do(run_research_pipeline)
    
    logging.info("Scheduled research pipeline to run daily at 2:00 AM")
    print("Scheduled research pipeline to run daily at 2:00 AM")
    print("Press Ctrl+C to stop the scheduler")
    
    # Keep the scheduler running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            print("\n Scheduler stopped by user")
            break
        except Exception as e:
            logging.error(f"Scheduler error: {str(e)}")
            print(f"Scheduler error: {str(e)}")
            time.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Research Pipeline - Run once or schedule daily')
    parser.add_argument('--schedule', action='store_true', 
                       help='Start scheduler to run daily at 2 AM')
    parser.add_argument('--test-schedule', action='store_true',
                       help='Test scheduler (runs every 2 minutes)')
    
    args = parser.parse_args()
    
    if args.schedule:
        # Start the daily scheduler
        start_scheduler()
    elif args.test_schedule:
        # Test scheduler (runs every 2 minutes for testing)
        setup_logging()
        print("Starting TEST scheduler (every 2 minutes)")
        schedule.every(2).minutes.do(run_research_pipeline)
        
        # Run once immediately for testing
        print("Running once immediately...")
        run_research_pipeline()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n Test scheduler stopped")
                break
    else:
        # Run once (original behavior)
        setup_logging()
        result = run_research_pipeline()

if __name__ == "__main__":
    main()