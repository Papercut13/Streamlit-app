import streamlit as st
st.set_page_config(page_title="Analysis App", layout="wide")  # Must be the very first Streamlit command


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from nepal_trafficking_scraper import NepalTraffickingScraper
import os

# =============================================================================
# CUSTOM CSS FOR THEME
# =============================================================================
st.markdown(
    """
    <style>
    /* Overall background for the app */
    .stApp {
        background-color: #f8f8f2;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #e8f5e9;
    }
    /* Home page button styling */
    div.stButton > button {
        background-color: #4b6c5d;
        color: white;
        padding: 2rem 3rem !important;
        font-size: 1.5rem !important;
        border-radius: 0.5rem !important;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #3a594f;
        color: white;
    }
    /* Header styling */
    h1, h2, h3, h4, h5, h6 {
        color: #4b6c5d;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# DATA LOADING & PROCESSING
# =============================================================================
@st.cache_data
def load_data():
    data = pd.read_csv('UNESCO_edu_data.csv')
    metadata = pd.read_csv('SDG_METADATA.csv')
    
    # Processing and combining data on Indicator ID and Indicator Label
    data.drop('indicator_desc', inplace=True, axis=1)
    data.rename(columns={'indicator_id': 'INDICATOR_ID'}, inplace=True)
    data['INDICATOR_ID'] = data['INDICATOR_ID'].str.upper().str.strip()
    
    # Merge with metadata
    label_data = pd.merge(data, metadata, on="INDICATOR_ID", how="left")
    return label_data

# Load and cache the data
label_data = load_data()

# =============================================================================
# NAVIGATION SETUP
# =============================================================================
PARENTS = {
    "Nepal": "individual",
    "Estonia": "individual",
    "Sierra Leone": "individual",
    "USA": "individual",
    "individual": "home",
    "cross": "home",
    "trafficking": "home"
}

def show_back_button():
    """Display a 'Go Back' button in the sidebar (unless on the Home page)."""
    if st.session_state.page != "home":
        if st.sidebar.button("Go Back"):
            st.session_state.page = PARENTS[st.session_state.page]

# =============================================================================
# INDIVIDUAL ANALYSIS: MULTISELECT-ENABLED LINE CHART
# =============================================================================
def create_line_chart_with_selection(country_code):
    """
    For the selected country, display a multiselect widget for the user to choose which
    indicator(s) (variable) to display. Each option shows the indicator ID along with its label.
    Returns a Plotly line chart with the selected indicators.
    """
    df = label_data[label_data['country_id'] == country_code]
    unique_indicators = df[['INDICATOR_ID', 'INDICATOR_LABEL_EN']].drop_duplicates().sort_values('INDICATOR_ID')
    
    # List of indicator IDs for the multiselect options
    indicator_options = unique_indicators['INDICATOR_ID'].tolist()
    
    # Custom format function to display indicator id along with its label
    def format_indicator(ind):
        label = unique_indicators[unique_indicators['INDICATOR_ID'] == ind]['INDICATOR_LABEL_EN'].iloc[0]
        return f"{ind} - {label}"
    
    selected_indicators = st.multiselect(
        "Select Indicator(s) to Display",
        options=indicator_options,
        format_func=format_indicator,
        default=[]  # default to all if you wish; otherwise, set to [] for none
    )
    
    if not selected_indicators:
        st.warning("Please select at least one indicator.")
        return None

    # Filter the dataframe to only include the selected indicators
    df_filtered = df[df['INDICATOR_ID'].isin(selected_indicators)]
    
    fig = px.line(
        df_filtered,
        x='year',
        y='value',
        color='INDICATOR_ID',
        markers=True,
        custom_data=['INDICATOR_LABEL_EN'],
        template='plotly_white',
        labels={'year': 'Year', 'value': 'Value'},
        height=700
    )
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>Year: %{x}<br>Value: %{y}<extra></extra>'
    )
    fig.update_layout(margin=dict(l=60, r=60, t=40, b=80))
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=5, label='Last 5 Years', step='year', stepmode='backward'),
                dict(count=10, label='Last 10 Years', step='year', stepmode='backward'),
                dict(step='all', label='All Years')
            ]
        )
    )
    return fig

# =============================================================================
# PAGE FUNCTIONS
# =============================================================================
def show_home():
    """Home page with large buttons to select analysis type."""
    st.title("Home")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual Analysis", use_container_width=True):
            st.session_state.page = "individual"
    with col2:
        if st.button("Cross-country Analysis", use_container_width=True):
            st.session_state.page = "cross"
    with col3:
        if st.button("Nepal Human Trafficking Data", use_container_width=True):
            st.session_state.page = "trafficking"

def show_individual():
    """Individual Analysis page with buttons for each country."""
    st.title("Individual Analysis")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nepal", use_container_width=True):
            st.session_state.page = "Nepal"
        if st.button("USA", use_container_width=True):
            st.session_state.page = "USA"
    with col2:
        if st.button("Estonia", use_container_width=True):
            st.session_state.page = "Estonia"
        if st.button("Sierra Leone", use_container_width=True):
            st.session_state.page = "Sierra Leone"

def show_cross():
    """Cross-country Analysis page with indicator selection and multiple visualization types."""
    st.title("Cross-country Analysis")
    
    # Define the indicators with their descriptions
    indicators = {
        "EA.3T8.AG25T99": "Educational attainment rate, completed upper secondary education or higher, population 25+ years, both sexes (%)",
        "XGOVEXP.IMF": "Expenditure on education as a percentage of total government expenditure (%)",
        "XGDP.FSGOV": "Government expenditure on education as a percentage of GDP (%)",
        "XUNIT.PPPCONST.2T3.FSGOV.FFNTR": "Initial government funding per secondary student, constant PPP$",
        "NER.02.CP": "Net enrolment rate, pre-primary, both sexes (%)",
        "ROFST.1T3.CP": "Out-of-school rate for children, adolescents and youth of primary, lower secondary and upper secondary school age, both sexes (%)",
        "ROFST.1T3.F.CP": "Out-of-school rate for children, adolescents and youth of primary, lower secondary and upper secondary school age, female (%)",
        "ROFST.1T3.M.CP": "Out-of-school rate for children, adolescents and youth of primary, lower secondary and upper secondary school age, male (%)",
        "ROFST.H.3": "Out-of-school rate for youth of upper secondary school age, both sexes (household survey data) (%)",
        "ROFST.3.F.CP": "Out-of-school rate for youth of upper secondary school age, female (%)",
        "ROFST.3.M.CP": "Out-of-school rate for youth of upper secondary school age, male (%)",
        "SCHBSP.2.WELEC": "Proportion of lower secondary schools with access to electricity (%)",
        "SCHBSP.1.WCOMPUT": "Proportion of primary schools with access to computers for pedagogical purposes (%)",
        "SCHBSP.1.WELEC": "Proportion of primary schools with access to electricity (%)",
        "SCHBSP.2T3.WCOMPUT": "Proportion of secondary schools with access to computers for pedagogical purposes (%)",
        "SCHBSP.3.WELEC": "Proportion of upper secondary schools with access to electricity (%)"
    }
    
    # Create a selectbox for indicator selection.
    selected_indicator = st.selectbox(
        "Select an Indicator",
        options=list(indicators.keys()),
        format_func=lambda x: f"{x} - {indicators[x]}"
    )
    
    st.write(f"Displaying cross-country analysis for: **{indicators[selected_indicator]}**")
    
    # Extra space between text and graph
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Filter data for the selected indicator
    df = label_data[label_data["INDICATOR_ID"] == selected_indicator].drop_duplicates()
    
    # Define a discrete color mapping for the countries
    color_map = {
        "NPL": "#FF6347",   # Tomato red
        "USA": "#000080",   # Navy blue
        "SLE": "#FFDB58",   # Mustard yellow
        "EST": "#4682B4"    # Steel blue
    }
    
    viz_tabs = st.tabs(["Line Chart", "Area Chart", "Bar Chart"])
    
    with viz_tabs[0]:
        fig_line = px.line(
            df,
            x="year",
            y="value",
            color="country_id",
            markers=True,
            template="plotly_white",
            labels={"year": "Year", "value": "Value", "country_id": "Country"},
            color_discrete_map=color_map,
            height=700
        )
        fig_line.update_layout(margin=dict(l=60, r=60, t=40, b=80))
        fig_line.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=[
                    dict(count=5, label="Last 5 Years", step="year", stepmode="backward"),
                    dict(count=10, label="Last 10 Years", step="year", stepmode="backward"),
                    dict(step="all", label="All Years")
                ]
            )
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    with viz_tabs[1]:
        fig_area = px.area(
            df,
            x="year",
            y="value",
            color="country_id",
            template="plotly_white",
            labels={"year": "Year", "value": "Value", "country_id": "Country"},
            color_discrete_map=color_map,
            height=700
        )
        # Reduce opacity for area chart
        fig_area.update_traces(opacity=0.75)
        fig_area.update_layout(margin=dict(l=60, r=60, t=40, b=80))
        fig_area.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=[
                    dict(count=5, label="Last 5 Years", step="year", stepmode="backward"),
                    dict(count=10, label="Last 10 Years", step="year", stepmode="backward"),
                    dict(step="all", label="All Years")
                ]
            )
        )
        st.plotly_chart(fig_area, use_container_width=True)
    
    with viz_tabs[2]:
        df_bar = df.groupby(["year", "country_id"])["value"].mean().reset_index()
        fig_bar = px.bar(
            df_bar,
            x="year",
            y="value",
            color="country_id",
            barmode="group",
            template="plotly_white",
            labels={"year": "Year", "value": "Average Value", "country_id": "Country"},
            color_discrete_map=color_map,
            height=700
        )
        fig_bar.update_layout(margin=dict(l=60, r=60, t=40, b=80))
        st.plotly_chart(fig_bar, use_container_width=True)

# =============================================================================
# INDIVIDUAL ANALYSIS PAGES (USING MULTISELECT FOR INDICATOR SELECTION)
# =============================================================================
def show_nepal():
    st.title("Nepal Analysis")
    fig = create_line_chart_with_selection('NPL')
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

def show_estonia():
    st.title("Estonia Analysis")
    fig = create_line_chart_with_selection('EST')
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

def show_sierra_leone():
    st.title("Sierra Leone Analysis")
    fig = create_line_chart_with_selection('SLE')
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

def show_usa():
    st.title("USA Analysis")
    fig = create_line_chart_with_selection('USA')
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# NEPAL HUMAN TRAFFICKING DATA PAGE
# =============================================================================
def show_trafficking():
    """Nepal Human Trafficking Data page with scraper functionality."""
    st.title("Nepal Human Trafficking Data Scraper")
    
    st.markdown("""
    This page allows you to scrape human trafficking data related to Nepal from various reliable sources
    and export the data to spreadsheet format.
    """)
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Data Sources")
        st.markdown("""
        The scraper collects data from the following sources:
        - **UN Office on Drugs and Crime (UNODC)** - Global reports on trafficking in persons
        - **US State Department** - Trafficking in Persons (TIP) Report
        - **International Labour Organization (ILO)** - Forced labor and child labor statistics
        - **Nepal Police** - Local law enforcement data
        - **Ministry of Women, Children and Senior Citizens** - Government victim protection data
        - **National Human Rights Commission Nepal** - Human rights violations reports
        - **NGOs** - Maiti Nepal, Shakti Samuha, and other organizations working on trafficking issues
        """)
    
    with col2:
        st.subheader("Actions")
        
        # Initialize scraper in session state
        if 'scraper' not in st.session_state:
            st.session_state.scraper = NepalTraffickingScraper()
            st.session_state.scraped_data = None
        
        # Scrape data button
        if st.button("🔍 Scrape Latest Data", use_container_width=True):
            with st.spinner("Scraping data from multiple sources..."):
                try:
                    data = st.session_state.scraper.scrape_all_sources()
                    st.session_state.scraped_data = data
                    st.success(f"Successfully scraped {len(data)} data points!")
                except Exception as e:
                    st.error(f"Error scraping data: {str(e)}")
        
        # Export buttons
        if st.session_state.scraped_data:
            st.subheader("Export Data")
            
            col_excel, col_csv = st.columns(2)
            
            with col_excel:
                if st.button("📊 Export to Excel", use_container_width=True):
                    with st.spinner("Creating Excel file..."):
                        try:
                            excel_file = st.session_state.scraper.save_to_excel()
                            if excel_file and os.path.exists(excel_file):
                                with open(excel_file, 'rb') as f:
                                    st.download_button(
                                        label="Download Excel File",
                                        data=f.read(),
                                        file_name="nepal_trafficking_data.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                                st.success("Excel file ready for download!")
                        except Exception as e:
                            st.error(f"Error creating Excel file: {str(e)}")
            
            with col_csv:
                if st.button("📄 Export to CSV", use_container_width=True):
                    with st.spinner("Creating CSV file..."):
                        try:
                            csv_file = st.session_state.scraper.save_to_csv()
                            if csv_file and os.path.exists(csv_file):
                                with open(csv_file, 'r') as f:
                                    st.download_button(
                                        label="Download CSV File",
                                        data=f.read(),
                                        file_name="nepal_trafficking_data.csv",
                                        mime="text/csv",
                                        use_container_width=True
                                    )
                                st.success("CSV file ready for download!")
                        except Exception as e:
                            st.error(f"Error creating CSV file: {str(e)}")
    
    # Display scraped data
    if st.session_state.scraped_data:
        st.subheader("Scraped Data Preview")
        
        # Create DataFrame for display
        df = pd.DataFrame(st.session_state.scraped_data)
        
        # Show summary statistics
        summary = st.session_state.scraper.get_summary_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", summary.get('total_records', 0))
        with col2:
            st.metric("Data Sources", summary.get('sources', 0))
        with col3:
            st.metric("Years Covered", summary.get('years_covered', 0))
        with col4:
            st.metric("Categories", summary.get('categories', 0))
        
        # Show data table
        st.dataframe(df, use_container_width=True)
        
        # Create visualizations
        if 'source' in df.columns:
            st.subheader("Data Visualization")
            
            # Chart by source
            source_counts = df['source'].value_counts()
            fig_source = px.bar(
                x=source_counts.index, 
                y=source_counts.values,
                title="Number of Data Points by Source",
                labels={'x': 'Source', 'y': 'Number of Records'}
            )
            fig_source.update_layout(
                xaxis_tickangle=-45,
                height=400
            )
            st.plotly_chart(fig_source, use_container_width=True)
            
            # Chart by category if available
            if 'category' in df.columns:
                category_counts = df['category'].value_counts()
                fig_category = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title="Distribution by Category"
                )
                st.plotly_chart(fig_category, use_container_width=True)
            
            # Timeline chart if year data is available
            if 'year' in df.columns and 'value' in df.columns:
                # Filter numeric values for timeline
                numeric_df = df[pd.to_numeric(df['value'], errors='coerce').notna()].copy()
                numeric_df['value'] = pd.to_numeric(numeric_df['value'])
                
                if not numeric_df.empty:
                    fig_timeline = px.line(
                        numeric_df,
                        x='year',
                        y='value',
                        color='indicator',
                        title="Timeline of Key Indicators",
                        labels={'value': 'Value', 'year': 'Year'}
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)

# =============================================================================
# MAIN APP FUNCTION
# =============================================================================
def main():
    if "page" not in st.session_state:
        st.session_state.page = "home"
    show_back_button()
    
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "individual":
        show_individual()
    elif st.session_state.page == "cross":
        show_cross()
    elif st.session_state.page == "trafficking":
        show_trafficking()
    elif st.session_state.page == "Nepal":
        show_nepal()
    elif st.session_state.page == "Estonia":
        show_estonia()
    elif st.session_state.page == "Sierra Leone":
        show_sierra_leone()
    elif st.session_state.page == "USA":
        show_usa()

if __name__ == "__main__":
    main()
