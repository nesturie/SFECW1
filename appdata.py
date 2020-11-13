# Import the neccesary packages to run this app. The packages can be downloaded with pip install from the command prompt
import streamlit as st
import pandas as pd
import plotly_express as px
import pydeck as pdk
import matplotlib.pyplot as plt


# Upon loading dashboard, load and process the global death data
#The structure of the data is taken from files shared for free from Johns Hopkins University to
# The data used in this program is dummy data. The structure on the other hand it is taken from JH University. 

@st.cache  #(information about how this part of the code works is taken from the streamlit guidelines on ""how to get started with streamlit ")
def load_global_death_data():
    # Pull data from csv file that contains the same format of data of Johns Hopkins University source
   data = pd.read_csv('time_series_covid19_confirmed_global.csv')
   # Drop columns province/state, geographic coordinates. Take the Latitude and the Longtitude from the CSV file that is located in the same folder as the python application
   data.drop(['Province/State', 'Lat', 'Long'], axis=1, inplace=True)
   # Groupby country. In the CSV file there is included a list of countries. Data = dat.groupby will collect the information and will group the regions of the United Kingdom from the CSV file.
   data = data.groupby(['Country/Region']).sum()
   return data

# Function to be used for plotting the global deaths data with a line graph
# Global plot create is a function that will plot the data of the death results in the csv file and will convert them into a graph.
def global_plot_create(data, x, y, title, xaxis, yaxis):
    fig = px.line(data, x=x, y=y, color='Country/Region', width=1000, height=800) # we assign the size of the plot, assigning the width and the height.
    fig.update_layout(title=title, # in this part we assign the layout to include the xaxis and yaxis
                      xaxis_title= xaxis, 
                      yaxis_title = yaxis,
                      legend_title_text='Countries',
                      yaxis_type="log", 
                      yaxis_tickformat = 'f',
                      xaxis_gridcolor = 'LightGreen', # the grid will make the line that appears on graph to be more flexible to be studied
                      yaxis_gridcolor = 'LightGreen',
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig
#_________________________________________________________________________________________________________________________________



# the following function will pull the data from the csv file
def load_uk_death_data():
    # Pull data from csv file located in the same folder as the python file.
   data =  pd.read_csv('time_series_covid19_confirmed_UK.csv')
   # The unused columns will be dropped by using data.drop
   data.drop(['Country_Region','UID','iso2','iso3','code3','Combined_Key','FIPS','Admin2','Lat', 'Long_', 'Population'], axis=1, inplace=True)
   # Groupby state
   data = data.groupby(['Province_State']).sum()
   return data


def date_conversion(df):
    # this function will convert the data therefore we will start to transpose the frame
    df_tran = df.transpose().reset_index()
    # Next step is to rename the columns 
    df_tran.rename({'index': 'Date'}, axis=1, inplace=True)
    # following with converting the date column to datetime
    df_tran['Date'] =  pd.to_datetime(df_tran['Date'])
    return df_tran

def death_data(df,group):
    df_tidy = pd.melt(df, id_vars=['Date'])
    df_tidy.drop(df_tidy[df_tidy['value'] < 10].index, inplace=True) # Drop all dates and countries with less than 10 recorded deaths
    df_tidy = df_tidy.assign(Days=df_tidy.groupby(group).Date.apply(lambda x: x - x.iloc[0]).dt.days) # Calculate the number of days since 10th death by country
    # calculate daily change in deaths (raw)
    df_tidy['daily_change'] = df_tidy.sort_values([group,'Days']).groupby(group)['value'].diff()
    # calculate daily change in deaths, final result to be appearing in percentage %
    df_tidy['daily_pct_change'] = df_tidy.sort_values([group,'Days']).groupby(group)['value'].pct_change() * 100
    # calculate 7-day rolling average in deaths (raw)
    df_tidy['daily_roll_avg'] = df_tidy.groupby(group)['daily_change'].rolling(7).mean().round().reset_index(0,drop= True)
    # calculate 7-day rolling average in deaths (%)
    df_tidy['daily_pctchange_roll_avg'] = df_tidy.groupby(group)['daily_pct_change'].rolling(7).mean().round().reset_index(0,drop= True)

    # Replace the first day (NaN) as zero and missing rolling averages with the value that day
    df_tidy['daily_change'].fillna(0, inplace=True)
    df_tidy['daily_pct_change'].fillna(0, inplace=True)
    df_tidy['daily_roll_avg'].fillna(df_tidy['daily_change'], inplace=True)
    df_tidy['daily_pctchange_roll_avg'].fillna(df_tidy['daily_pct_change'], inplace=True)
    return df_tidy



# Function to be used for plotting the UK confirmed cases data with a line graph
def us_plot_create(data, x, y, title, xaxis, yaxis):
    fig = px.line(data, x=x, y=y, color='Province_State', width=1000, height=800)
    fig.update_layout(title=title, 
                      xaxis_title= xaxis, 
                      yaxis_title = yaxis,
                      legend_title_text='United Kingdom',
                      yaxis_type="log", 
                      yaxis_tickformat = 'f',
                      xaxis_gridcolor = 'LightGreen',
                      yaxis_gridcolor = 'LightGreen',
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig

# Main function runs the app automatically when called
def main():

    page = st.sidebar.selectbox("Choose a dataset", ['United Kingdom Map', 'Global'])



    if page == 'Global':

        # Process all of the global death data using the created functions
        global_data = load_global_death_data()
        global_data = date_conversion(global_data)
        global_deaths = death_data(global_data, group = 'Country/Region')

        st.title('Global COVID-19 Deaths')
        st.header('Daily COVID-19 deaths by country from Jan 22, 2020 - Present.')
        st.write("Raw Data:", global_data)

        # Create a list to pick the countries we want to look at
        # list uses the column names (the countries) of our original data
        cols = list(global_data[global_data.columns.difference(['Date'])])
        countries = st.multiselect('Select countries display', cols, ["United Kingdom"])

        # Set index in order to use loc operation
        global_deaths.set_index('Country/Region', inplace=True)
        # Limit the data to the countries selected above. 
        data_plot = global_deaths.loc[countries] 
        data_plot.reset_index(inplace=True)

        # Select the variable to be plotted, this will appear as a drop down option when the variable is selected.
        cols = ['Total Confirmed Deaths', 'Deaths per Day','Daily Percentage Change']
        variable = st.selectbox('Select variable to display', cols)

        if variable == 'Total Confirmed Deaths':
            fig=global_plot_create(data = data_plot, 
                        x = 'Days',
                        y = 'value',
                        title = 'Global COVID-19 Deaths - Total',
                        xaxis = 'Number of days since 10th death',
                        yaxis = 'Confirmed Deaths')
            st.plotly_chart(fig)

        elif variable == 'Deaths per Day':
            fig=global_plot_create(data = data_plot, 
                        x = 'Days',
                        y = 'daily_roll_avg',
                        title = 'Daily Confirmed Deaths (7 day rolling average)',
                        xaxis = 'Number of days since 10th death',
                        yaxis = 'Confirmed Daily Deaths')
            st.plotly_chart(fig)
        else:
            fig2=global_plot_create(data = data_plot, 
                        x = 'Days',
                        y = 'daily_pctchange_roll_avg',
                        title = 'Daily Confirmed Deaths Growth (%)',
                        xaxis = 'Number of days since 10th death',
                        yaxis = 'Rate Change (%)')
            # Daily growth plot doesn't need a logged axis, so update the plot accordingly
            fig2.update_layout(yaxis_type="linear")

            st.plotly_chart(fig2)



                        
    else:
        st.title('UK Map')

        # Read in fresh dataframe of UK deaths data
        uk_deaths = pd.read_csv('time_series_covid19_confirmed_UK.csv')
        
        # Drop rows with missing coordinates and any NaN values
        uk_deaths = uk_deaths[(uk_deaths['Lat'] != 0)]
        uk_deaths.dropna(inplace=True)

        # BELOW USED FOR SLIDER IN SELECTING DAY COUNT
        date_count = uk_deaths.iloc[:,50:]
        max_days = len(date_count.columns)
        day = st.slider("Days since March 1, 2020", 1, max_days - 1, max_days - 1)
        
        # Create a list of column names (the dates) for display purposes
        date_list = list(uk_deaths.iloc[:,50:])

        # Display the corresponding date of the day count since March 1, 2020
        date_selection = date_list[day]
        st.subheader(date_selection)


        st.header('Deaths by UK territory as of ' + str(uk_deaths[date_selection].name))

        # Replace latest date of data column with the 'value' title to visualize
        uk_deaths.columns = uk_deaths.columns.str.replace(uk_deaths[date_selection].name, "value")

        # Calculate a color ramp to use
        uk_deaths['Color'] = uk_deaths['value'].map(lambda x: [int(255*c) for c in  plt.cm.Wistia(x/2000)])

       
        # Create a pydeck map object that will update as we change our slider THIS SECTION CONSISTS ON CREATING  MAP 
        st.pydeck_chart(pdk.Deck(
                     map_style="mapbox://styles/mapbox/dark-v10",
                     mapbox_key = 'pk.eyJ1IjoicnVzc2hvd2QiLCJhIjoiY2puOTJpNmh5MHZjdTNwbXNxdDlyYTdmciJ9.C_p9lRLmh_J50bLDr2eScA',
                     tooltip={    
                            'html': '<b> {Combined_Key} </b> <br> <b>Deaths:</b> {value} ',
                            'style': {
                                    'color': 'white'
                                    }
                            },
                    initial_view_state={    # GIVING COORDINATES TO DETERMINE THE INITAL POSITION OF THE MAP
                    "latitude": 52,
                    "longitude": -1.92, 
                    "zoom": 4,
                    "pitch": 70,
                    "bearing": -37,
                },
                layers=[
                    pdk.Layer(
                       'ColumnLayer',
                        data=uk_deaths,
                            get_position=["Long_", "Lat"],
                            get_elevation="value / 2",
                            elevation_scale=500,
                            radius=7000,
                            get_fill_color='Color',
                            auto_highlight=True,
                            pickable=True,
                            material=True),
                    ],
                ))
if __name__ == '__main__':
    main()
