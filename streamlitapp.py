import streamlit as st
import plotly.express as px
import psycopg2
import pandas as pd
st.title('Tennis Gamming Analysis')
connection = psycopg2.connect(
    host="localhost",
    database="MDTm37",
    user="postgres",        
    password="post38"
)
cursor = connection.cursor()

section =st.sidebar.radio('Navigation',['Home','search and Filter competitors','competitor details',
                                 'country wise analysis','Leader boards','venues and complexes'])

if section =="Home":
    st.subheader('Overview')
    st.write("""This interactive dashboard provides comprehensive insights into the world of tennis, 
         analyzing rankings, competitors, countries, venues, and complexes. """)
    
    cursor.execute('select COUNT(*) AS total_no_of_competitors from competitors_table')
    result = cursor.fetchall()
    st.success(f"Total number of competitors: {result}")

    cursor.execute('SELECT country FROM competitors_table')  # Execute the query O
    countries = [row[0] for row in cursor]  # Fetch ALL the data into a list
    num_countries = len(set(countries))   # Count the unique countries
    st.success(f'Number of countries represented: {num_countries}')  # Display the count

    cursor.execute("""SELECT c.name AS competitor, r.points FROM competitor_rankings_table r JOIN competitors_table c 
                   ON r.competitor_id = c.competitor_id
            WHERE r.points = (SELECT MAX(points) FROM competitor_rankings_table);""")
    high_points=cursor.fetchone()
    st.success(f"Highest_points_by_competitor:{high_points}")
    # Create a bar plot for highest points by competitor (you can adjust for multiple competitors if needed)
    fig_high_points = px.bar(x=[high_points[1]], y=[high_points[0]], labels={'x': 'Competitor', 'y': 'Points'},
                            title="Highest Points by Competitor")    
    st.plotly_chart(fig_high_points)
 # competitions Details
    st.subheader('competitions Details')
    cursor.execute("""SELECT c.competition_name AS competitions,c.competition_type,c.competition_gender AS Gender,cat.category_name FROM competition_table c 
    JOIN categories cat ON c.category_id=cat.category_id;  """)
    result_c = cursor.fetchall()
    df=pd.DataFrame(result_c,columns=['competitions','competition_type','Gender','category_name'])
    st.dataframe(df)  
   
if section == "search and Filter competitors":
    cursor.execute("""SELECT c.name, r.rank 
                      FROM competitors_table c 
                      JOIN competitor_rankings_table r 
                      ON c.competitor_id = r.competitor_id;""")
    all_competitor_names = [row[0] for row in cursor.fetchall()]

    # Create a multiselect widget to choose competitors
    selected_competitor = st.multiselect('Select Competitor(s)', all_competitor_names)

    if selected_competitor:
        df_selected_competitors = pd.DataFrame({'Competitor': selected_competitor})
        st.dataframe(df_selected_competitors)  # Display selected competitors

        # Prepare the IN clause for the SQL query if there are selected competitors
        placeholders = ", ".join(["%s"] * len(selected_competitor))
        query = f"""
            SELECT r.rank, r.points, c.country 
            FROM competitor_rankings_table r 
            JOIN competitors_table c ON r.competitor_id = c.competitor_id
            WHERE c.name IN ({placeholders})
        """

        cursor.execute(query, tuple(selected_competitor))
        results = cursor.fetchall()

        if results:
            df = pd.DataFrame(results, columns=['Rank', 'Points', 'Country'])
            st.write(df)

            # Create a Plotly figure (optional, but good for visualization)
            fig = px.bar(df, x='Country', y='Points', color='Country', title='Points by Country')
            st.plotly_chart(fig)
    else:
        st.write("Please select at least one competitor.")

if section=="competitor details":
    cursor.execute("SELECT name FROM competitors_table")
    names=[row[0] for row in cursor.fetchall()] 
    
    competitor_name = st.selectbox('competitor_name',names)
    st.write(competitor_name)
   
    if competitor_name in names:
        cursor.execute("""SELECT r.rank,r.movement,r.competitions_played,c.country FROM 
                        competitor_rankings_table r join competitors_table c on r.competitor_id=c.competitor_id
                        WHERE c.name=%s;""",(competitor_name,))
                        
        cr=cursor.fetchall()
        df_c=pd.DataFrame(cr,columns=['rank','movement','competitions_played','country'])
        st.write(df_c)   
    
if section =="country wise analysis":
    cursor.execute("""SELECT c.country AS countries,COUNT(c.name) AS total_number_of_competitors,AVG(r.points) as average_points FROM 
                   competitor_rankings_table r join competitors_table  c on r.competitor_id=c.competitor_id GROUP BY c.country;
                   """)
    country_data = cursor.fetchall()
    
    df_country = pd.DataFrame(country_data, columns=['Country', 'Total Competitors', 'Average Points'])
    st.write(df_country)
    # ploting
    fig=px.bar(df_country,x='Country',y='Total Competitors',title ='Total competitors by country',color='Total Competitors')
    st.plotly_chart(fig)
    fig1=px.bar(df_country,x='Country',y='Average Points',title ='Average Points by country',color='Average Points')
    st.plotly_chart(fig1)
    
    
# Leader boards
if section == 'Leader boards':
    n_top = st.number_input("enter the top rank:", min_value=1, max_value=501, value=100)
    if n_top:
        cursor.execute("""SELECT r.rank AS top_rank, c.name FROM competitor_rankings_table r
                          JOIN competitors_table c ON r.competitor_id = c.competitor_id
                          WHERE r.rank <= %s ORDER BY r.rank DESC""", (n_top,))
        res = cursor.fetchall()

        df = pd.DataFrame(res, columns=['top_rank', 'name'])
        for index, row in df.iterrows():
            top_rank = row['top_rank']
            name = row['name']
        st.write(df)
    # competitor with highest pointsS
    st.header('competitor with highest points')
    cursor.execute("""SELECT MAX(r.points) AS Highest_points,c.name AS competitor FROM competitor_rankings_table r
                          JOIN competitors_table c ON r.competitor_id = c.competitor_id
                          Group By c.name""")
    resultp = cursor.fetchall()
    df_p=pd.DataFrame(resultp,columns=['Hidhest_points','competitor'])
    st.dataframe(df_p)
    
## VENUES AND COMPLEXES
if section =='venues and complexes':
    st.subheader('VENUES AND COMPLEXES')
    cursor.execute("""SELECT v.venue_name,v.city_name,v.country_name,v.time_zone,c.complex_name FROM venues_table v join 
                complexes c on v.complex_id=c.complex_id;""")
    vc=cursor.fetchall()
    df_v=pd.DataFrame(vc,columns=['venue_name','city','country','time_zone','complex_name'])
    st.write(df_v)
    # Chart (venues vs. complexes)
    fig1 = px.bar(df_v, x="venue_name", y="time_zone",color = 'complex_name',title="Venues vs timezone")
    st.plotly_chart(fig1)
    fig = px.histogram(df_v, x='time_zone', title="Distribution of Time Zones Across Venues", labels={'time_zone': 'Time Zone'})
    # Display the histogram plot
    st.plotly_chart(fig)
    