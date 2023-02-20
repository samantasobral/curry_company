#Libraries
from haversine import haversine
import pandas as pd
import numpy as np
import plotly.express as px
import folium
import streamlit as st
import regex as re
from PIL import Image
from streamlit_folium import folium_static
from datetime import datetime

#-------------------------------------
#Funções
#-------------------------------------

def clean_code(df):
    """ Esta função tem a responsabilidade de limpar o dataframe
        
        Tipos de limpeza:
        1.Remoção dos dados NaN
        2.Mudança do tipo da coluna de dados
        3.Remoção dos espaços das variáveus de texto
        4.Formatação da coluna de datas
        5.Limpeza da coluna de tempo(remoção do texto da variável numérica)
        
        Input: Dataframe
        Output: Dataframe
    """
    
    # Remover spaco da string
    df['ID'] = df['ID'].str.strip()
    df['Delivery_person_ID'] = df['Delivery_person_ID'].str.strip()

    # Excluir as linhas com a idade dos entregadores vazia
    # ( Conceitos de seleção condicional )
    linhas_vazias = df['Delivery_person_Age'] != 'NaN '
    df = df.loc[linhas_vazias, :]

    # Conversao de texto/categoria/string para numeros inteiros
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype( int )

    # Conversao de texto/categoria/strings para numeros decimais
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype( float )

    # Conversao de texto para data
    df['Order_Date'] = pd.to_datetime( df['Order_Date'], format='%d-%m-%Y' )

    # Remove as linhas da culuna multiple_deliveries que tenham o 
    # conteudo igual a 'NaN '
    linhas_vazias = df['multiple_deliveries'] != 'NaN '
    df = df.loc[linhas_vazias, :]
    df['multiple_deliveries'] = df['multiple_deliveries'].astype( int )

    # Comando para remover o texto de números
    df = df.reset_index( drop=True )

    # Retirando os espaços da coluna Festival
    df['Festival'] = df['Festival'].str.strip()

    #removendo "NaN" da cidade e do transito
    df = df.loc[df['City'] != 'NaN ', :]
    df = df.loc[df['Road_traffic_density'] != 'NaN ', :]
    
    #limpando a coluna de timetaken
    df['Time_taken(min)'] = df['Time_taken(min)'].apply(lambda x: x.split('(min)') [1])
    df['Time_taken(min)'] = df['Time_taken(min)'].astype(int)
    
    df['week_of_year'] = df['Order_Date'].dt.strftime( "%U" )
    
    return df

def top_delivers(df1, top_asc):
            
    df_aux = df1.loc[:, ['City','Delivery_person_ID', 'Time_taken(min)']].groupby(['City', 'Delivery_person_ID']).mean().sort_values(['Time_taken(min)', 'City'], ascending = top_asc).reset_index()
    df_aux1 = df_aux.loc[df_aux['City'] == 'Metropolitian ', :].head(10)
    df_aux2 = df_aux.loc[df_aux['City'] == 'Urban ', :].head(10) 
    df_aux3 = df_aux.loc[df_aux['City'] == 'Semi-Urban ', :].head(10)
    df_aux4 = pd.concat([df_aux1, df_aux2, df_aux3]).reset_index(drop = True)
    return(df_aux4)

#------------------------------Estrutura lógica do código--------------------
#---------------------
#importando o arquivo
#---------------------
df = pd.read_csv('dataset\train.csv')

#-------------------
#limpando os dados
#-------------------
df1 = clean_code(df)

#VISÃO ENTREGADORES
 
#=====================================
#layout no streamlit - BARRA LATERAL
#=====================================
st.header('Marketplace - Visão Entregadores')

image = Image.open('pc2.jpg')
st.sidebar.image(image, width=120)

st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""---""")

st.sidebar.markdown('## Selecione uma data limite')
date_slider = st.sidebar.slider(
    'Até qual data?', 
    value=pd.datetime(2022, 4, 13),
    min_value=pd.datetime(2022, 2, 11),
    max_value=pd.datetime(2022, 4, 6),
    format='DD-MM-YYYY')
st.sidebar.markdown("""---""")

traffic_options = st.sidebar.multiselect(
    'Quais as condições do trânsito?',
    ['Low ', 'Medium ', 'High ', 'Jam '],
    default= ['Low ', 'Medium ', 'High ', 'Jam '])
st.sidebar.markdown("""---""")

clima = st.sidebar.multiselect(
    'Quais as condições do clima?',
    ['conditions Cloudy', 'conditions Fog', 'conditions Sandstorms', 'conditions Stormy', 'conditions Sunny', 'conditions Windy'],
    default= ['conditions Cloudy', 'conditions Fog', 'conditions Sandstorms', 'conditions Stormy', 'conditions Sunny', 'conditions Windy'])

#filtro das datas:
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]

#filtro de trânsito:
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]

#filtro do clima:
linhas_selecionadas = df1['Weatherconditions'].isin(clima)
df1 = df1.loc[linhas_selecionadas, :]

#================================
#layout no streamlit
#================================

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', '_', '_'])

with tab1:
    with st.container():
        st.title('Overall Metrics')
        
        col1, col2, col3, col4 = st.columns(4, gap='large')
        with col1:
            st.subheader('Mais velho')
            velho = df1.loc[:,'Delivery_person_Age'].max()
            col1.metric('Idade', velho)
        
        with col2:
            st.subheader('Mais novo')
            novo = df1.loc[:, 'Delivery_person_Age'].min()
            col2.metric('Idade', novo)
        
        with col3:
            st.subheader('Veículo')
            melhor = df1.loc[:,'Vehicle_condition'].max()
            col3.metric('Melhor condição', melhor)
        
        with col4:
            st.subheader('Veículo')
            pior = df1.loc[:,'Vehicle_condition'].min()
            col4.metric('Pior condição', pior)
    
    with st.container():
        st.markdown("""---""")
        st.title('Avaliações')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('##### Avaliação média por entregador')
            cols = ['Delivery_person_Ratings', 'Delivery_person_ID']
            df_aux = df1.loc[:,cols].groupby('Delivery_person_ID').mean().reset_index()
            st.dataframe(df_aux)
        
        with col2:
            st.markdown('##### Avaliação média por trânsito')
            cols = ['Delivery_person_Ratings', 'Road_traffic_density']
            df_avg_rating_by_traffic = df1.loc[:,cols].groupby('Road_traffic_density').mean().reset_index()
            st.dataframe(df_avg_rating_by_traffic)
            
            st.markdown('##### Avaliação média por clima')
            cols = ['Delivery_person_Ratings', 'Weatherconditions']
            df_avg_rating_by_weather = df1.loc[:,cols].groupby('Weatherconditions').mean().reset_index()
            st.dataframe(df_avg_rating_by_weather)
    
    with st.container():
        st.markdown("""---""")
        st.title('Velocidade de Entrega')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('##### Top Entregadores mais rápidos')
            df_aux4 = top_delivers(df1, top_asc = True)            
            st.dataframe(df_aux4)
        
        with col2:
            st.markdown('##### Top Entregadores mais lentos')
            df_aux4 = top_delivers(df1, top_asc = False)            
            st.dataframe(df_aux4)
            
