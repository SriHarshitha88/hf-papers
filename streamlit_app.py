import streamlit as st
from src.research_crew.crew import ResearchCrew
from supabase import create_client
import pandas as pd
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI Research Papers Dashboard",
    page_icon="📚",
    layout="wide"
)

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_ANON_KEY')
    )

supabase = init_supabase()

# Sidebar
st.sidebar.title("🤖 Research Papers AI")
st.sidebar.markdown("---")

# Main content
st.title("📚 AI Research Papers Dashboard")
st.markdown("Automated research paper collection and summarization using CrewAI")

# Action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Fetch Latest Papers", type="primary"):
        with st.spinner("Processing latest papers..."):
            try:
                crew = ResearchCrew()
                result = crew.run()
                st.success("✅ Successfully processed papers!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    if st.button("📊 Refresh Dashboard"):
        st.rerun()

with col3:
    if st.button("🗑️ Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")

# Display papers
st.markdown("---")
st.subheader("📋 Recent Research Papers")

# Fetch papers from database
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_papers():
    try:
        response = supabase.table('research_papers').select('*').order('created_at', desc=True).limit(20).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching papers: {str(e)}")
        return []

papers = fetch_papers()

if papers:
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        categories = list(set([p.get('category', 'Unknown') for p in papers]))
        selected_category = st.selectbox("Filter by Category", ['All'] + categories)
    
    with col2:
        search_term = st.text_input("🔍 Search papers", placeholder="Enter keywords...")
    
    # Filter papers
    filtered_papers = papers
    if selected_category != 'All':
        filtered_papers = [p for p in filtered_papers if p.get('category') == selected_category]
    
    if search_term:
        filtered_papers = [p for p in filtered_papers if 
                          search_term.lower() in p.get('title', '').lower() or 
                          search_term.lower() in p.get('technical_summary', '').lower()]
    
    # Display papers
    for paper in filtered_papers:
        with st.expander(f"📄 {paper.get('title', 'No Title')}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Category:** {paper.get('category', 'Unknown')}")
                st.markdown(f"**Technical Summary:** {paper.get('technical_summary', 'No summary available')}")
                
                if paper.get('key_contributions'):
                    st.markdown("**Key Contributions:**")
                    for contrib in paper.get('key_contributions', []):
                        st.markdown(f"• {contrib}")
                
                if paper.get('methodology'):
                    st.markdown(f"**Methodology:** {paper.get('methodology')}")
                
                if paper.get('significance'):
                    st.markdown(f"**Significance:** {paper.get('significance')}")
            
            with col2:
                if paper.get('paper_url'):
                    st.markdown(f"[📖 Read Paper]({paper.get('paper_url')})")
                
                if paper.get('authors'):
                    st.markdown("**Authors:**")
                    for author in paper.get('authors', []):
                        st.markdown(f"• {author}")
                
                if paper.get('tags'):
                    st.markdown("**Tags:**")
                    st.markdown(", ".join(paper.get('tags', [])))
                
                st.markdown(f"**Added:** {paper.get('created_at', '')[:10]}")

else:
    st.info("No papers found. Click 'Fetch Latest Papers' to get started!")

# Statistics
if papers:
    st.markdown("---")
    st.subheader("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Papers", len(papers))
    
    with col2:
        categories = [p.get('category', 'Unknown') for p in papers]
        st.metric("Categories", len(set(categories)))
    
    with col3:
        today_papers = [p for p in papers if p.get('created_at', '')[:10] == str(datetime.now().date())]
        st.metric("Today's Papers", len(today_papers))
    
    with col4:
        avg_summary_length = sum(len(p.get('technical_summary', '')) for p in papers) / len(papers)
        st.metric("Avg Summary Length", f"{int(avg_summary_length)} chars") 