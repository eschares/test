# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 16:58:12 2021

@author: eschares
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import streamlit_analytics
import streamlit.components.v1 as components

#streamlit_analytics.start_tracking()


st.markdown(
    """
      <!-- Global site tag (gtag.js) - Google Analytics -->
      <script async src="https://www.googletagmanager.com/gtag/js?id=G-FDDMR7WRFB"></script>
      <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
    
        gtag('config', 'G-FDDMR7WRFB');
      </script>
    
      <!-- Global site tag (gtag.js) - Google Analytics -->
      <script async src="https://www.googletagmanager.com/gtag/js?id=UA-196264375-1"></script>
      <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

        gtag('config', 'UA-196264375-1');
      </script>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
<h1>Eric s</h1>
    """,
    unsafe_allow_html=True
)


components.html(
    """
    <head>
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-195227159-1"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'UA-195227159-1');
    </script>
    </head>
    """
)




st.image('unsub_extender2.png')

my_slot2 = st.empty()   #save this spot to fill in later for filename to analyze

#Initialize with a hardcoded dataset
file = filename = "Unsub_export_example.csv"


uploaded_file = st.sidebar.file_uploader('Upload new .csv file to analyze:', type='csv')

if uploaded_file is not None:
    file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
    #st.write(file_details)
    
    file = uploaded_file
    filename = uploaded_file.name

my_slot2.subheader('TEST file "' + filename + '"')

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_data(file):
    st.write("I ran!")
    return pd.read_csv(file, sep=',', encoding='utf-8')  #Process the data

df = load_data(file)

# #force 'subscribed' column to be a string, not Bool and all uppercase
df['subscribed'] = df['subscribed'].astype(str)
df['subscribed'] = df['subscribed'].str.upper()


#process data to calculate IF%
total_usage = df['usage'].sum()
df['current_yr_usage'] = ((df['use_ill_percent'] + df['use_other_delayed_percent']) / 100) * df['usage']
df['IF%'] = (df['current_yr_usage'] / total_usage) * 100
df['cost_per_IF%'] = df['subscription_cost'] / df['IF%']

sidebar_modifier_slot = st.sidebar.empty()
col1, col2 = st.beta_columns(2)

price_slider = st.sidebar.slider('Price ($) between:', min_value=0, max_value=int(max(df['subscription_cost'])), value=(0,int(max(df['subscription_cost']))))
cpu_slider = st.sidebar.slider('Cost per Use Rank between:', min_value=0, max_value=int(max(df['cpu_rank'])), value=(0,int(max(df['cpu_rank']))))
filt = ( (df['cpu_rank'].between(cpu_slider[0], cpu_slider[1])) &
         (df['subscription_cost'].between(price_slider[0], price_slider[1]))
        )

st.write('filt is', filt)

summary_df = df[filt].groupby('subscribed')['subscription_cost'].agg(['count','sum'])
summary_df['sum'] = summary_df['sum'].apply(lambda x: "${0:,.0f}".format(x))
#now formatted as a string (f)
#leading dollar sign, add commas, round result to 0 decimal places
st.write(summary_df.sort_index(ascending=False))

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(df[filt])

# #set up the color maps on 'subscribed'
subscribed_colorscale = alt.Scale(domain = ['TRUE', 'FALSE', 'MAYBE', ' '],
                                  range = ['blue', 'red', 'green', 'gray'])



#Put Modifier down here after the filt definition so only those titles that meet the filt show up, but put into empty slot further up the sidebar for flow
with sidebar_modifier_slot:
    with st.beta_expander("Change a journal's Subscribed status:"):
        #df.set_index('title', inplace=True)
        selected_titles = st.multiselect('Journal Name:', pd.Series(df.loc[filt]['title']), help='Displayed in order provided by the underlying datafile')
        #eric_filt = (df['title']=="Bioresource Technology")
        st.write('you selected',selected_titles)
        #df.reset_index(inplace=True)
        
        #Somehow when df gets filtered, then journal titles refer to original indexes which don't exist
        #Make new df that overwrites old every time?
        #reset indexes?
        #referring to oringinal index 5, not the new number like 2 in the filtered df...
    
        col1, col2 = st.beta_columns([2,1])
    
        with col1:
            radiovalue = st.radio("Change 'Subscribed' status to:", ['TRUE', 'MAYBE', 'FALSE', '(blank)'])
            if radiovalue == "(blank)":
                radiovalue = " "
                #write(radiovalue)
        with col2:
            st.write(" ")       #Move the Commit button down vertically
            st.write(" ")       #I'm sure there's a smarter way to do this, but oh well
            if st.button('Commit change!'):
                for title in selected_titles:
                    title_filter = (df['title'] == title)
                    df.loc[title_filter, 'subscribed'] = radiovalue



# click = alt.selection_multi(encodings=['color'])


#weighted usage in log by cost (x), colored by subscribed
#adding clickable legend to highlight subscribed categories
selection1 = alt.selection_multi(fields=['subscribed'], bind='legend')
weighted_vs_cost = alt.Chart(df[filt], title='Weighted Usage vs. Cost by Subscribed status, clickable legend').mark_circle(size=75, opacity=0.5).encode(
    alt.X('subscription_cost:Q', axis=alt.Axis(format='$,.2r')),
    alt.Y('usage:Q', scale=alt.Scale(type='log'), title='Weighted Usage (DL + Cit + Auth)'),
    color=alt.condition(selection1, alt.Color('subscribed:N', scale=subscribed_colorscale), alt.value('lightgray')),   #Nominal data type
    tooltip=['title','downloads','citations','authorships','usage','subscription_cost', 'cpu_rank', 'subscribed'],
    ).interactive().properties(height=500).add_selection(selection1)
st.altair_chart(weighted_vs_cost, use_container_width=True)


unsub_hist = alt.Chart(df[filt].reset_index()).mark_bar().encode(
    alt.X('cpu:Q', bin=alt.Bin(maxbins=100), title="Cost per Use bins", axis=alt.Axis(format='$')),
    alt.Y('count()', axis=alt.Axis(grid=False)),
    alt.Detail('index'),
    tooltip=['title', 'cpu'],
    #color='subscribed',
    color=alt.Color('subscribed:N', scale=subscribed_colorscale)
    ).properties(
        title={
            "text": ["Unsub's Cost per Use Histogram, color coded by Subscribed status"],
            "subtitle": ["Graph supports pan, zoom, and live-updates from changes in filters on the left"],
            "color": "black",
            "subtitleColor": "gray"
        },
        height=450,
        width=900
).interactive()
unsub_hist
#col1.header("COL1")
#col1.write(unsub_hist)
#col2.header("COL2")
#col2.write(summary_df)





#same chart as above but now colored by cpu_rank, and would really like buckets somehow
selection2 = alt.selection_multi(fields=['cpu_rank'], bind='legend')
weighted_vs_cost2 = alt.Chart(df[filt], title='Weighted Usage vs. Cost by CPU_Rank').mark_circle(size=75, opacity=0.5).encode(
    alt.X('subscription_cost:Q', axis=alt.Axis(format='$,.2r')),
    y=alt.Y('usage:Q', scale=alt.Scale(type='log'), title='Weighted Usage (DL + Cit + Auth)'),
    color=alt.condition(selection2, alt.Color('cpu_rank:Q', scale=alt.Scale(scheme='viridis')), alt.value('lightgray')
        #,legend = alt.Legend(type='symbol')                
        ),   #selection, if selected, if NOT selected
    #opacity=alt.condition(selection2, alt.value(1), alt.value(0.2)),
    tooltip=['title','downloads','citations','authorships','usage','subscription_cost', 'cpu_rank', 'subscribed'],
    ).interactive().properties(height=500).add_selection(selection2)
st.altair_chart(weighted_vs_cost2, use_container_width=True)



hist = alt.Chart(df).mark_bar(size=30).encode(
    alt.X('subscribed', sort='-y'), #sort=alt.EncodingSortField(field='subscribed', op='count', order='descending')),
    alt.Y('count():Q'),
    color=alt.Color('subscribed:N', scale=subscribed_colorscale)    #can't figure out how to sort the x-axis
    #column=alt.Column(sort=["TRUE","MAYBE","FALSE"," "])
    ).properties(width=300).interactive()

text = alt.Chart(df).mark_text(dx=-1, dy=-10, color='black').encode(
    alt.X('subscribed'),
    alt.Y('count()'),
    #detail=('subscribed'),
    text=alt.Text('sum(subscription_cost):Q', format='$,.2f')
)

hist + text

# hist = alt.Chart(df).mark_bar().encode(
#     x='count()',
#     y='subscribed',
#     color = alt.condition(click, alt.Color('subscribed:N', scale=subscribed_colorscale), alt.value('lightgray'))
# ).add_selection(click)
        
# unsub_hist & hist




# #click the bar chart to filter the scatter plot
# click = alt.selection_multi(encodings=['color'])
# scatter = alt.Chart(df, title="Citations vs. Downloads, with clickable bar graph linked underneath").mark_point().encode(
#     x='downloads',
#     y='citations',
#     color='subscribed'
# ).transform_filter(click).interactive()

# hist = alt.Chart(df).mark_bar().encode(
#     x='count()',
#     y='subscribed',
#     color = alt.condition(click, alt.Color('subscribed:N', scale=subscribed_colorscale), alt.value('lightgray'))
# ).add_selection(click)

# #scatter & hist





#scatter matrix
# scatter_selection = alt.selection_multi(fields=['subscribed'], bind='legend')

# eric = alt.Chart(df).mark_circle().encode(
#     alt.X(alt.repeat("column"), type='quantitative'),
#     alt.Y(alt.repeat("row"), type='quantitative'),
#     #color=alt.Color('subscribed:N', scale=subscribed_colorscale)
#     color=alt.condition(scatter_selection, alt.Color('subscribed:N', scale=subscribed_colorscale), alt.value('lightgray')),   #Nominal data type
#     tooltip=['title','downloads','citations','authorships','weighted usage','subscription_cost', 'cpu_rank', 'subscribed']    
# ).properties(
#     width=350,
#     height=250
# ).repeat(
#     row=['weighted usage'],#, 'downloads', 'citations', 'authorships'],
#     column=['downloads', 'citations', 'authorships']
# ).interactive().add_selection(scatter_selection)

# eric

streamlit_analytics.stop_tracking()

#st.altair_chart(eric, use_container_width=True)



