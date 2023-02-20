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
import plotly.graph_objects as go

#--------------------------------
#FUNÇÕES
#--------------------------------

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


def distance(df1):
#calcular a distância entre os restaurantes (fim) e locais de entrega(inicio)
    cols = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude' ]
    df1['distance'] = df1.loc[:, cols].apply( lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']),(x['Delivery_location_latitude'],x['Delivery_location_longitude']) ), axis=1)
#calcular a distância média 
    df02 = np.round(df1.loc[:,'distance'].mean(), 2)
    return df02

def avg_std_time_delivery(df1, op, festival):
    """ esta função calcula o tempo médio e o desvio padrão do tempo de entrega no Festival.
          Parêmetros:
            Input: 
                df: dataframe
                op: tipo de operação a ser calculada:
                    'Time_mean': calcula o tempo médio
                    'Time_std': calcula o desvio padrão
                    Output: dataframe com duas colunas e 1 linha
    """
    df_aux = df1.loc[:, ['Time_taken(min)', 'Festival']].groupby('Festival').agg({'Time_taken(min)': ['mean', 'std']})
    df_aux.columns = ['Time_mean', 'Time_std']
    df_aux = df_aux.reset_index()
    df_aux = np.round(df_aux.loc[df_aux['Festival'] == festival, op], 2)
    return df_aux


def avg_time_delivery_city(df1):
    cols = ['Time_taken(min)', 'City']
    df_aux = df1.loc[:,cols].groupby('City').agg({'Time_taken(min)': ['mean', 'std']})
    df_aux.columns = ['Time_mean', 'Time_std']
    df_aux = df_aux.reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(name = 'Control',x=df_aux['City'], y=df_aux['Time_mean'], error_y=dict(type='data', array=df_aux['Time_std'])))
    fig.update_layout(barmode='group')
    return fig

def avg_distance(df1):
    st.title('Distância média dos restaurantes e dos locais de entrega por cidade')
    cols = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude' ]
    df1['distance'] = df1.loc[:, cols].apply( lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']),(x['Delivery_location_latitude'],x['Delivery_location_longitude']) ), axis=1)
    df02 = df1.loc[:,['City','distance']].groupby('City').mean().reset_index()
    fig = go.Figure(data =[go.Pie(labels=df02['City'], values=df02['distance'], pull=[0,0.1,0])])
    return fig

def avg_std_time_city_traffic(df1):
    df_aux = df1.loc[:, ['Time_taken(min)', 'City', 'Road_traffic_density']].groupby(['City', 'Road_traffic_density']).agg({'Time_taken(min)': ['mean', 'std']})
    df_aux.columns = ['Time_mean', 'Time_std']
    df_aux = df_aux.reset_index()
    fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'], values='Time_mean', color = 'Time_std', color_continuous_scale='Rdbu', color_continuous_midpoint = np.average(df_aux['Time_std']))
    return fig


def std_distance(df1):
    df_aux = (df1.loc[:,['Time_taken(min)', 'City', 'Type_of_order']].groupby(['City', 'Type_of_order']).agg({'Time_taken(min)': ['mean', 'std']}))
    df_aux.columns = ['Time_mean', 'Time_std']
    df_aux = df_aux.reset_index()
    return df_aux

#------------------------------------Início da estrutura lógica do código ---------------------------
#-----------------------
#importando o arquivo
#---------------------
df = pd.read_csv(r'C:\Users\samso\repos_cds\ftc\train.csv')

#-----------------------
#limpando os dados
#-----------------------
df1 = clean_code(df)

#VISÃO RESTAURANTES
 
#================================
#layout no streamlit - barra lateral
#================================
st.header('Marketplace - Visão Restaurantes')

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


#VISÃO RESTAURANTES

#================================
#layout no streamlit
#================================

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', '_', '_'])

with tab1:
    with st.container():
        st.title('Overal Metrics')
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown('###### Entregadores')
            delivery_unique = len(df1.loc[:,'Delivery_person_ID'].unique())
            col1.metric('Quantidade', delivery_unique)
        
        with col2:
            st.markdown('###### Distância Km')
            df02 = distance(df1)
            col2.metric('Média', df02)
            
        with col3:
            #06. o tempo médio de entrega durante os festivais
            st.markdown('###### Com festival')
            df_aux = avg_std_time_delivery(df1,'Time_mean', 'Yes')
            col3.metric('Tempo médio (min)', df_aux)
            
        
        with col4:
            #06. Desvio padrão de entrega durante os festivais
            st.markdown('###### Com festival')
            df_aux = avg_std_time_delivery(df1, 'Time_std', 'Yes')
            col4.metric('Desvio padrão', df_aux)
            
        with col5:
            st.markdown('###### Sem festival')
            df_aux = avg_std_time_delivery(df1, 'Time_mean', 'No')
            col5.metric('Tempo médio (min)', df_aux)
        
        with col6:
            st.markdown('###### Sem festival')
            df_aux = avg_std_time_delivery(df1, 'Time_std', 'No')
            col6.metric('Desvio padrão', df_aux) 
    
    with st.container():
        st.markdown("""___""")
        fig = avg_distance(df1)
        st.plotly_chart(fig, use_container_width = True)
          
    with st.container():
        st.markdown("""___""")
        st.title('Distribuição do tempo')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('##### Tempo médio de entrega por cidade')
            fig=avg_time_delivery_city(df1)
            st.plotly_chart(fig, use_container_width = True)
            
        with col2:
            st.markdown('##### O tempo médio e o desvio padrão de entrega por cidade e tipo de tráfego')
            fig = avg_std_time_city_traffic(df1)
            st.plotly_chart(fig, use_container_width = True)            
            
        
    with st.container():
        st.markdown("""___""")
        st.title('Distibuição da distância')
        df_aux = std_distance(df1)
        st.dataframe(df_aux)