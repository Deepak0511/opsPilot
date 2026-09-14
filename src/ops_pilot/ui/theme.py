import streamlit as st

def apply_enterprise_theme():
    """Apply professional, restrained CSS styling to the Streamlit app."""
    css = """
    <style>
    /* Base typography adjustments for a more professional feel */
    .stMarkdown, .stText, p {
        font-size: 15px !important;
    }

    /* Restrained header hierarchy */
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
    }
    h3 {
        font-size: 1.25rem !important;
        font-weight: 500 !important;
    }

    /* Improve chat message density */
    [data-testid="stChatMessage"] {
        padding: 0.75rem 1rem !important;
        gap: 0.75rem !important;
    }

    /* Main content width and padding */
    [data-testid="stAppViewBlockContainer"] {
        max-width: 960px !important; 
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Sidebar refinement */
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 350px !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    /* Code blocks / json output adjustments */
    .stCodeBlock {
        font-size: 13px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
