#Libraries
from haversine import haversine
import pandas as pd
import numpy as np
import plotly.express as px
import folium
import streamlit as st
import re
from PIL import Image
from streamlit_folium import folium_static
from datetime import datetime

#-----------------------------------------------
# FUNÇÕES 
#-----------------------------------------------
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

def orders_by_day(df1):
    #01. Quantidade de pedidos por dia
    df01 = df1.loc[:,['ID', 'Order_Date']].groupby('Order_Date')
    df01a = df01.count().reset_index()
    fig = px.bar(df01a, x='Order_Date', y = 'ID')
    return fig

def traffic_order_share(df1):
    #03.Distribuição dos pedidos por tipo de tráfego
#grafico de pizza
    cols = ['ID','Road_traffic_density']
    df_aux = df1.loc[:, cols].groupby('Road_traffic_density').count().reset_index()
    df_aux = df_aux.loc[df_aux['Road_traffic_density'] != 'NaN ', :]  #excluindo o NaN
    df_aux['entregas_perc'] = df_aux['ID']/df_aux['ID'].sum() #calculando o %
    fig = px.pie(df_aux, values='ID', names ='Road_traffic_density')
    return fig

def traffic_order_city(df1):
    #04.Comparação do volume de pedidos por cidade e tipo de tráfego
#grafico de bolha (tMamanho da bolha é a qtde de entregas)
    cols =['ID', 'City', 'Road_traffic_density']
    df_aux = df1.loc[:, cols].groupby(['City', 'Road_traffic_density']).count().reset_index()
    df_aux = df_aux.loc[df_aux['City'] != 'NaN ', :]
    df_aux = df_aux.loc[df_aux['Road_traffic_density'] != 'NaN ', :]
    fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size = 'ID', color = 'City')
    return fig

def order_week(df1):
    #02.Quantidade de pedidos por semana
    #criar a coluna de semana 'week_of_year'
    df1['week_of_year'] = df1['Order_Date'].dt.strftime('%U') #%U significa começando a semana por domingo, %W por segunda-feira
    df_aux = df1.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
    fig = px.line(df_aux, x='week_of_year', y='ID')
    return fig

def order_share_week(df1):
    #05.A quantidade de pedidos por entregador por semana: qtde de pedidos por semana / numeros de entregadores únicos por semana
    #grafico de linhas
    #número de pedidos por semana:
        
    df_aux1 = df1.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
    df_aux2 = df1.loc[:, ['Delivery_person_ID', 'week_of_year']].groupby('week_of_year').nunique().reset_index()
    #unindo as duas tabelas:
    df_aux = pd.merge(df_aux1, df_aux2, how='inner')
    #criando a coluna qtde pedidos / n. entregadores:
    df_aux['order_by_person'] = df_aux['ID'] / df_aux['Delivery_person_ID']
    fig = px.line(df_aux, x='week_of_year', y='order_by_person')
    return fig

def country_map(df1):
    #06.A localização central de cada cidade por tipo de tráfego
#mapa
    cols = ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude' ]
    df_aux = df1.loc[:, cols]. groupby(['City', 'Road_traffic_density']).median().reset_index()
    df_aux = df_aux.loc[df_aux['City'] != 'NaN ', :]
    df_aux = df_aux.loc[df_aux['Road_traffic_density'] != 'NaN ', :]

    map = folium.Map()

    for index, location_info in df_aux.iterrows():
        folium.Marker([location_info['Delivery_location_latitude'], location_info['Delivery_location_longitude']], popup = location_info[['City', 'Road_traffic_density']]).add_to(map)

    folium_static(map, width = 1024 , height= 600)
    return None

#------------------------------------Início da estrutura lógica do código ---------------------------
#-----------------------
#importando o arquivo
#---------------------
df = pd.read_csv('..dataset/train.csv')

#-----------------------
#limpando os dados
#-----------------------
df1 = clean_code(df)
    

#VISÃO EMPRESA
 
#================================
#layout no streamlit - barra lateral
#================================
st.header('Marketplace - Visão Empresa')

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

#filtro das datas:
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]

#filtro de trânsito:
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]


#================================
#layout no streamlit
#================================

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    with st.container():
        st.header('Orders by Day')
        fig = orders_by_day(df1)
        st.plotly_chart(fig, use_container_width = True)
        
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.header('Traffic Order Share')
            fig = traffic_order_share(df1)
            st.plotly_chart(fig, use_container_width = True)
        
        with col2:
            st.header('Traffic Order by City')
            fig = traffic_order_city(df1)
            st.plotly_chart(fig, use_container_width = True)
    
with tab2:
    with st.container():
        st.header("Order by Week")
        fig = order_week(df1)
        st.plotly_chart(fig, use_container_width = True)
    
    with st.container():
        st.header("Order Share by Week")
        fig = order_share_week(df1)
        st.plotly_chart(fig, use_container_width=True)
    
    
with tab3:
    st.header("Country Map")
    country_map(df1)
    
