import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration for a better UI
st.set_page_config(page_title="Housing Affordability Agent", page_icon="🏘️", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #e3f2fd;
    }
    h1, h2, h3 {
        color: #1e3d59;
    }
    .metric-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #ff6e40;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏘️ Charlottesville Housing Affordability Agent")
st.markdown("Analyze property values and find affordable neighborhoods in Charlottesville, Virginia.")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("/Users/ep9k/Desktop/charlottesville_assessments_with_neighborhoods.csv")
        # Ensure CurrentAssessedValue is numeric
        df['CurrentAssessedValue'] = pd.to_numeric(df['CurrentAssessedValue'], errors='coerce')
        # Drop rows with severe missing data if necessary, here we just keep non-null assessments
        df = df.dropna(subset=['CurrentAssessedValue', 'neighborhood'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data loaded. Please check the dataset file path.")
else:
    # --- City Overview ---
    st.header("📍 City Overview")
    
    total_parcels = len(df)
    median_value = df['CurrentAssessedValue'].median()
    mean_value = df['CurrentAssessedValue'].mean()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Total Parcels</div><div class="metric-value">{total_parcels:,}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Median Parcel Value</div><div class="metric-value">${median_value:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Mean Parcel Value</div><div class="metric-value">${mean_value:,.2f}</div></div>', unsafe_allow_html=True)
        
    st.subheader("Distribution of Parcel Values")
    # Filter out extreme outliers for better visualization, e.g., keep 99th percentile
    upper_limit = df['CurrentAssessedValue'].quantile(0.99)
    fig_hist = px.histogram(df[df['CurrentAssessedValue'] <= upper_limit], 
                            x='CurrentAssessedValue', 
                            nbins=50,
                            labels={'CurrentAssessedValue': 'Parcel Value ($)'},
                            color_discrete_sequence=['#ff6e40'])
    fig_hist.update_layout(bargap=0.1, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_hist, use_container_width=True)
    
    st.markdown("---")
    
    # --- Neighborhood Analysis ---
    st.header("🏘️ Neighborhood Analysis")
    
    # Aggregate data by neighborhood
    neighborhood_stats = df.groupby('neighborhood').agg(
        Total_Parcels=('CurrentAssessedValue', 'count'),
        Median_Value=('CurrentAssessedValue', 'median'),
        Mean_Value=('CurrentAssessedValue', 'mean')
    ).reset_index()
    
    # Sort by median value (lowest to highest) for affordability ranking
    neighborhood_stats = neighborhood_stats.sort_values('Median_Value')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Neighborhoods Ranked by Affordability")
        st.dataframe(
            neighborhood_stats.style.format({
                'Median_Value': '${:,.2f}',
                'Mean_Value': '${:,.2f}'
            }), 
            use_container_width=True,
            hide_index=True
        )
        
    with col2:
        st.subheader("Median Parcel Value by Neighborhood")
        fig_bar = px.bar(neighborhood_stats, 
                         x='Median_Value', 
                         y='neighborhood', 
                         orientation='h',
                         labels={'Median_Value': 'Median Value ($)', 'neighborhood': 'Neighborhood'},
                         color='Median_Value',
                         color_continuous_scale='Viridis')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.markdown("---")
    
    # --- Affordability Calculator ---
    st.header("💰 Affordability Calculator")
    st.markdown("Calculate which neighborhoods are affordable based on the assumption that a household can afford a home valued at exactly **3× their annual income**.")
    
    annual_income = st.number_input("Enter your annual household income ($):", min_value=0, value=75000, step=5000)
    
    if st.button("Calculate Affordability", type="primary"):
        threshold = annual_income * 3
        st.info(f"💡 Based on your income, your estimated affordable home value threshold is **${threshold:,.2f}**.")
        
        # Determine affordability for each neighborhood
        # A neighborhood is considered affordable if its median parcel value is <= threshold
        affordability_df = neighborhood_stats.copy()
        affordability_df['Is_Affordable'] = affordability_df['Median_Value'] <= threshold
        
        affordable_neighborhoods = affordability_df[affordability_df['Is_Affordable']]['neighborhood'].tolist()
        
        if affordable_neighborhoods:
            st.success(f"🎉 Great news! There are **{len(affordable_neighborhoods)}** affordable neighborhoods for your budget.")
            st.markdown("**Affordable Neighborhoods:** " + ", ".join(f"`{n}`" for n in affordable_neighborhoods))
        else:
            st.error("📉 Unfortunately, no neighborhoods have a median parcel value below your threshold. Consider adjusting your expected threshold or income.")
            
        st.subheader("Detailed Affordability Table")
        
        # Format the dataframe for display
        display_df = affordability_df.copy()
        display_df['Status'] = display_df['Is_Affordable'].apply(lambda x: "✅ Affordable" if x else "❌ Unaffordable")
        display_df = display_df[['neighborhood', 'Median_Value', 'Status']]
        
        st.dataframe(
            display_df.style.format({'Median_Value': '${:,.2f}'}), 
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    
    # --- Mortgage Officers ---
    st.header("🤝 Mortgage Officers")
    st.markdown("Looking to finance your new home? Here are some top-rated mortgage officers in the Charlottesville area who can help.")
    
    # Define mortgage officers data
    mortgage_officers_data = [
        {"Name": "Katie Shiers", "Company": "Guild Mortgage", "Phone": "(434) 260-0421", "Email": "katie.shiers@guildmortgage.net", "Website": "https://www.guildmortgage.com"},
        {"Name": "Kristin Sorokti", "Company": "Guild Mortgage", "Phone": "(434) 566-1370", "Email": "ksorokti@guildmortgage.net", "Website": "https://www.guildmortgage.com"},
        {"Name": "Kat Whindleton", "Company": "Guild Mortgage", "Phone": "(434) 218-5505", "Email": "kat.whindleton@guildmortgage.net", "Website": "https://www.guildmortgage.com"},
        {"Name": "Jason Crigler", "Company": "Crown Mortgage", "Phone": "(434) 975-5626", "Email": "jcrigler@crownmortgage.com", "Website": "https://www.charlottesvilledirectmortgage.com"},
        {"Name": "Tom Mahone", "Company": "Mahone Mortgage, LLC", "Phone": "(434) 531-1949", "Email": "tom@mahonemortgage.com", "Website": "https://www.mahonemortgage.com"},
        {"Name": "Larry Saunders", "Company": "NEXA Mortgage LLC", "Phone": "(434) 466-5662", "Email": "larry@larrysloans.com", "Website": "https://www.larrysloans.com"},
        {"Name": "Daniel MacDougall", "Company": "PrimeLending", "Phone": "(434) 760-1245", "Email": "dmacdougall@primelending.com", "Website": "https://www2.primelending.com"},
        {"Name": "Bill Hamrick", "Company": "C&F Mortgage Corporation", "Phone": "(434) 974-1450", "Email": "bhamrick@cfmortgagecorp.com", "Website": "https://www.cfmortgagecorp.com"},
        {"Name": "Tammy Wilt", "Company": "Atlantic Bay Mortgage", "Phone": "(434) 242-0046", "Email": "tammywilt@atlanticbay.com", "Website": "https://www.atlanticbay.com"},
        {"Name": "Nick Bolmey", "Company": "Truist Bank", "Phone": "(434) 996-3582", "Email": "nick.bolmey@truist.com", "Website": "https://www.truist.com"}
    ]
    
    officers_df = pd.DataFrame(mortgage_officers_data)
    
    # Display the dataframe with proper formatting and clickable website links
    st.dataframe(
        officers_df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website (Click to open)")
        }
    )
