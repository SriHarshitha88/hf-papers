import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
from collections import Counter
import requests
import json
from supabase import create_client, Client
from typing import List, Dict, Optional
import re
import os
import sys
from pathlib import Path

# ✅ Add src/research_crew to sys.path to enable absolute imports
SRC_PATH = Path(__file__).resolve().parent / "src" / "research_crew"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

# ✅ Now you can use imports like this (no dots!)
try:
    from crew import ResearchCrew
except ImportError as e:
    st.error(f"Could not import ResearchCrew: {e}")
    st.stop()


# Configure Streamlit page
st.set_page_config(
    page_title="CrewAI Research Paper Visualizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase configuration
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            st.error("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
            return None
            
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

def fetch_papers_from_db(supabase: Client, limit: int = 50) -> List[Dict]:
    """Fetch papers from Supabase database"""
    try:
        response = supabase.table('research_papers')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching papers from database: {e}")
        return []

def search_papers_in_db(supabase: Client, query: str, limit: int = 20) -> List[Dict]:
    """Search papers in database by title or summary"""
    try:
        response = supabase.table('research_papers')\
            .select('*')\
            .or_(f'title.ilike.%{query}%,summary.ilike.%{query}%,key_contributions.ilike.%{query}%')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error searching papers: {e}")
        return []

def filter_papers_by_category(supabase: Client, categories: List[str], limit: int = 50) -> List[Dict]:
    """Filter papers by categories"""
    try:
        category_filter = ','.join([f'"{cat}"' for cat in categories])
        response = supabase.table('research_papers')\
            .select('*')\
            .in_('category', categories)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error filtering papers: {e}")
        return []

def get_papers_by_date_range(supabase: Client, start_date: str, end_date: str) -> List[Dict]:
    """Get papers within a date range"""
    try:
        response = supabase.table('research_papers')\
            .select('*')\
            .gte('created_at', start_date)\
            .lte('created_at', end_date)\
            .order('created_at', desc=True)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching papers by date: {e}")
        return []

def process_crew_paper(paper: Dict) -> Dict:
    """Process paper data from CrewAI crew structure"""
    processed_paper = {
        'id': paper.get('id', ''),
        'title': paper.get('title', 'Untitled'),
        'authors': paper.get('authors', []) if isinstance(paper.get('authors'), list) else [paper.get('authors', 'Unknown')],
        'summary': paper.get('summary', paper.get('technical_summary', 'Summary not available')),
        'date': paper.get('published_date', paper.get('created_at', datetime.now().strftime('%Y-%m-%d'))),
        'url': paper.get('url', paper.get('arxiv_url', '')),
        'category': paper.get('category', 'Unknown'),
        'contributions': paper.get('key_contributions', []) if isinstance(paper.get('key_contributions'), list) else [paper.get('key_contributions', 'Contributions analysis pending')],
        'methodology': paper.get('methodology', 'Methodology details extracted from analysis'),
        'significance': paper.get('significance', 'Significance assessment completed by AI analysis'),
        'tags': paper.get('tags', []) if isinstance(paper.get('tags'), list) else [],
        'created_at': paper.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        'arxiv_id': paper.get('arxiv_id', ''),
        'technical_summary': paper.get('technical_summary', paper.get('summary', '')),
        'confidence_score': paper.get('confidence_score', 0.0)
    }
    
    # Process tags if they're stored as a string
    if isinstance(processed_paper['tags'], str):
        processed_paper['tags'] = [tag.strip() for tag in processed_paper['tags'].split(',') if tag.strip()]
    
    # Process contributions if stored as string
    if isinstance(processed_paper['contributions'], str):
        processed_paper['contributions'] = [contrib.strip() for contrib in processed_paper['contributions'].split('\n') if contrib.strip()]
    
    return processed_paper

def run_crew_analysis():
    """Run the CrewAI research crew to fetch and analyze new papers"""
    try:
        crew = ResearchCrew()
        result = crew.run()
        return result
    except Exception as e:
        st.error(f"Error running crew analysis: {e}")
        return None

def display_paper_card(paper: Dict, index: int):
    """Display an interactive paper card with crew-generated content"""
    
    # Main card container with enhanced styling
    with st.container():
        # Header section
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 🧠 {paper['title']}")
            authors_display = ', '.join(paper['authors'][:3]) + ('...' if len(paper['authors']) > 3 else '')
            st.markdown(f"**👥 Authors:** {authors_display}")
            
        with col2:
            st.markdown(f"**📅 Published:** {paper['date']}")
            category_emoji = "🤖" if paper.get('category') != 'Unknown' else "📂"
            st.markdown(f"**{category_emoji} Category:** {paper.get('category', 'Unknown')}")
            
            if paper.get('confidence_score'):
                st.markdown(f"**🎯 AI Confidence:** {paper['confidence_score']:.2f}")
            
            if paper.get('arxiv_id'):
                st.markdown(f"**🔗 arXiv:** {paper['arxiv_id']}")
        
        # Technical Summary (from CrewAI)
        with st.expander("🔬 Technical Summary (AI Generated)", expanded=True):
            st.write(paper.get('technical_summary', paper['summary']))
            
        # Key Contributions (from CrewAI analysis)
        with st.expander("🔑 Key Contributions (AI Analyzed)"):
            contributions = paper.get('contributions', [])
            if isinstance(contributions, list):
                for i, contrib in enumerate(contributions, 1):
                    st.markdown(f"{i}. {contrib}")
            else:
                st.write(contributions)
                
        # Methodology (from CrewAI analysis)
        with st.expander("🧪 Methodology (AI Extracted)"):
            st.write(paper.get('methodology', 'Methodology analysis in progress...'))
            
        # Significance Assessment (from CrewAI)
        with st.expander("🌟 Significance Assessment (AI Evaluated)"):
            st.write(paper.get('significance', 'Significance assessment pending...'))
        
        # Original Abstract
        if paper.get('summary') != paper.get('technical_summary'):
            with st.expander("📄 Original Abstract"):
                st.write(paper['summary'])
        
        # Tags and Metadata
        st.markdown("**🏷️ AI-Generated Tags:**")
        if paper.get('tags'):
            tags_cols = st.columns(min(len(paper['tags']), 4))
            for i, tag in enumerate(paper['tags'][:4]):
                with tags_cols[i % len(tags_cols)]:
                    st.markdown(f'<span style="background-color: #e1f5fe; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{tag}</span>', 
                              unsafe_allow_html=True)
        
        # Visualization section
        col_viz, col_meta = st.columns([2, 1])
        
        with col_viz:
            # Word cloud for tags and key terms
            if paper.get('tags'):
                try:
                    tags_text = " ".join(paper["tags"])
                    if len(tags_text) > 0:
                        wordcloud = WordCloud(width=300, height=150, background_color="white", 
                                            colormap='viridis').generate(tags_text)
                        fig, ax = plt.subplots(figsize=(6, 3))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis("off")
                        ax.set_title("Tag Cloud", fontsize=12)
                        st.pyplot(fig)
                        plt.close()
                except Exception as e:
                    st.warning("Could not generate word cloud")
        
        with col_meta:
            # Paper metadata
            if paper.get('url'):
                st.markdown(f"**🔗 [View Paper]({paper['url']})**")
            
            st.markdown(f"**📊 Authors:** {len(paper['authors'])}")
            st.markdown(f"**📝 Summary:** {len(paper['summary'].split())} words")
            st.markdown(f"**🕒 Added:** {paper.get('created_at', 'Unknown')[:10]}")
            
            # Quality indicators
            if paper.get('technical_summary'):
                st.markdown("✅ **AI Summary Generated**")
            if paper.get('contributions'):
                st.markdown("✅ **Contributions Analyzed**")

def show_dashboard(papers: List[Dict]):
    """Show analytics dashboard for crew-processed papers"""
    if not papers:
        st.sidebar.warning("No papers available")
        return
        
    st.sidebar.markdown("# 📈 CrewAI Dashboard")
    
    # Basic metrics
    st.sidebar.metric("📚 Total Papers", len(papers))
    
    # Category distribution
    categories = [p.get('category', 'Unknown') for p in papers]
    unique_categories = set(categories)
    st.sidebar.metric("📂 Categories", len(unique_categories))
    
    # Today's papers
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for p in papers if p.get("created_at", "")[:10] == today)
    st.sidebar.metric("🆕 Today's Papers", today_count)
    
    # AI-processed papers
    ai_processed = sum(1 for p in papers if p.get('technical_summary'))
    st.sidebar.metric("🤖 AI Processed", ai_processed)
    
    # Average summary length
    if papers:
        avg_summary_len = round(sum(len(p.get('summary', '').split()) for p in papers) / len(papers), 1)
        st.sidebar.metric("📝 Avg. Summary Length", f"{avg_summary_len} words")
    
    # Category distribution chart
    if len(unique_categories) > 1:
        st.sidebar.markdown("### 📊 Category Distribution")
        category_counts = Counter(categories)
        fig = px.pie(values=list(category_counts.values()), 
                    names=list(category_counts.keys()),
                    height=300,
                    color_discrete_sequence=px.colors.qualitative.Set3)
        st.sidebar.plotly_chart(fig, use_container_width=True)
    
    # Popular tags from AI analysis
    all_tags = []
    for paper in papers:
        if paper.get('tags'):
            all_tags.extend(paper['tags'])
    
    if all_tags:
        st.sidebar.markdown("### 🏷️ Popular AI Tags")
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(5)
        for tag, count in top_tags:
            st.sidebar.markdown(f"• **{tag}**: {count}")
    
    # Processing quality metrics
    st.sidebar.markdown("### 🎯 AI Processing Quality")
    has_contributions = sum(1 for p in papers if p.get('contributions'))
    has_methodology = sum(1 for p in papers if p.get('methodology'))
    has_significance = sum(1 for p in papers if p.get('significance'))
    
    st.sidebar.progress(has_contributions / len(papers), text=f"Contributions: {has_contributions}/{len(papers)}")
    st.sidebar.progress(has_methodology / len(papers), text=f"Methodology: {has_methodology}/{len(papers)}")
    st.sidebar.progress(has_significance / len(papers), text=f"Significance: {has_significance}/{len(papers)}")

def main():
    st.title("🤖 CrewAI Research Paper Visualizer")
    st.markdown("*Powered by CrewAI agents for intelligent paper collection and analysis*")
    
    # Initialize Supabase
    supabase = init_supabase()
    if not supabase:
        st.stop()
    
    # Initialize session state
    if 'papers' not in st.session_state:
        st.session_state.papers = []
    if 'last_fetch' not in st.session_state:
        st.session_state.last_fetch = None
    
    # Sidebar controls
    st.sidebar.markdown("# 🤖 CrewAI Controls")
    
    # Crew analysis button
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🚀 Run CrewAI Analysis", type="primary", help="Fetch new papers and run AI analysis"):
            with st.spinner("🤖 Running CrewAI research crew..."):
                result = run_crew_analysis()
                if result:
                    st.success("✅ CrewAI analysis completed!")
                    st.session_state.last_fetch = datetime.now()
                    # Force refresh of papers
                    st.session_state.papers = []
                else:
                    st.error("❌ CrewAI analysis failed")
    
    with col2:
        if st.button("🔄 Refresh Papers", help="Reload papers from database"):
            st.session_state.papers = []
            st.rerun()
    
    # Load papers from database if not in session state
    if not st.session_state.papers:
        with st.spinner("📥 Loading papers from database..."):
            papers = fetch_papers_from_db(supabase, limit=100)
            if papers:
                st.session_state.papers = [process_crew_paper(paper) for paper in papers]
                st.success(f"✅ Loaded {len(papers)} papers from database")
            else:
                st.info("No papers found in database. Run CrewAI analysis to fetch papers.")
    
    # Search and filter controls
    if st.session_state.papers:
        st.sidebar.markdown("# 🔍 Search & Filter")
        
        # Search functionality
        search_query = st.sidebar.text_input("🔎 Search Papers", 
                                           placeholder="Search by title, summary, or contributions...")
        
        if search_query:
            with st.spinner("Searching..."):
                search_results = search_papers_in_db(supabase, search_query)
                filtered_papers = [process_crew_paper(paper) for paper in search_results]
        else:
            filtered_papers = st.session_state.papers
        
        # Category filter
        all_categories = list(set(p.get('category', 'Unknown') for p in filtered_papers))
        selected_categories = st.sidebar.multiselect("📂 Categories", 
                                                   all_categories, 
                                                   default=all_categories)
        
        # Date filter
        st.sidebar.markdown("📅 Date Range")
        date_filter = st.sidebar.selectbox("Date Filter", 
                                         ["All Time", "Today", "This Week", "This Month"])
        
        # Apply filters
        if selected_categories != all_categories:
            filtered_papers = [p for p in filtered_papers 
                             if p.get('category', 'Unknown') in selected_categories]
        
        # Apply date filter
        if date_filter != "All Time":
            today = datetime.now()
            if date_filter == "Today":
                cutoff = today.strftime('%Y-%m-%d')
                filtered_papers = [p for p in filtered_papers 
                                 if p.get('created_at', '')[:10] == cutoff]
            elif date_filter == "This Week":
                week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                filtered_papers = [p for p in filtered_papers 
                                 if p.get('created_at', '')[:10] >= week_ago]
            elif date_filter == "This Month":
                month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                filtered_papers = [p for p in filtered_papers 
                                 if p.get('created_at', '')[:10] >= month_ago]
        
        # Show dashboard
        show_dashboard(filtered_papers)
        
        # Main content area
        if filtered_papers:
            st.markdown(f"## 📚 {len(filtered_papers)} Research Papers")
            
            # Sorting options
            col1, col2 = st.columns([3, 1])
            with col2:
                sort_by = st.selectbox("Sort by", 
                                     ["Newest First", "Oldest First", "Title A-Z", "Category"])
            
            # Sort papers
            if sort_by == "Newest First":
                filtered_papers.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            elif sort_by == "Oldest First":
                filtered_papers.sort(key=lambda x: x.get('created_at', ''))
            elif sort_by == "Title A-Z":
                filtered_papers.sort(key=lambda x: x.get('title', '').lower())
            elif sort_by == "Category":
                filtered_papers.sort(key=lambda x: x.get('category', ''))
            
            # Display stats
            with col1:
                ai_processed = sum(1 for p in filtered_papers if p.get('technical_summary'))
                st.markdown(f"**🤖 AI Processed:** {ai_processed}/{len(filtered_papers)} papers")
            
            st.markdown("---")
            
            # Display papers
            for i, paper in enumerate(filtered_papers):
                display_paper_card(paper, i)
                st.markdown("---")
                
        else:
            st.info("🔍 No papers match the current filters. Try adjusting your search or filters.")
    
    else:
        # Welcome screen
        st.info("👋 Welcome to CrewAI Research Paper Visualizer!")
        
        st.markdown("""
        ## 🎯 What this app does:
        
        **🤖 CrewAI Integration:**
        - Runs your AI research crew to fetch papers from HuggingFace Daily Papers
        - Processes papers using AI agents for analysis
        - Stores everything in your Supabase database
        
        **📊 Features:**
        - **Real-time paper fetching** from your CrewAI pipeline
        - **AI-generated summaries** and analysis
        - **Smart categorization** and tagging
        - **Advanced search** and filtering
        - **Interactive dashboards** with analytics
        - **Technical insights** extracted by AI agents
        
        **🔧 Your AI Crew:**
        - **Research Fetcher Agent**: Collects papers from sources
        - **Summarizer Agent**: Generates technical summaries
        - **Database Manager**: Stores and organizes papers
        
        👆 **Click "Run CrewAI Analysis" in the sidebar to get started!**
        """)
        
        # Show last fetch time if available
        if st.session_state.last_fetch:
            st.success(f"🕒 Last CrewAI run: {st.session_state.last_fetch.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()