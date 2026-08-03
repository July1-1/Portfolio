"""
Utilidades para visualización de mapas con Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
import numpy as np

from config import STATE_COORDINATES, COLORS
from data_processor import get_state_coordinates


def create_mexico_map(routes_data: List[Dict] = None, 
                     show_all_states: bool = True) -> go.Figure:
    """
    Crea un mapa interactivo de México con Plotly
    
    Args:
        routes_data: Lista de diccionarios con información de rutas
        show_all_states: Si True, muestra todos los estados
        
    Returns:
        Figura de Plotly
    """
    fig = go.Figure()
    
    # Configuración del mapa centrado en México
    fig.update_geos(
        scope='north america',
        center=dict(lat=23.6345, lon=-102.5528),
        projection_scale=4.5,
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor="lightgray",
        showcoastlines=True,
        coastlinecolor="gray",
        showland=True,
        landcolor="rgb(243, 243, 243)",
        showlakes=True,
        lakecolor="lightblue",
        showrivers=True,
        rivercolor="lightblue"
    )
    
    # Mostrar todos los estados si se solicita
    if show_all_states:
        states_df = pd.DataFrame([
            {
                'lat': coords['lat'],
                'lon': coords['lon'],
                'name': coords['name'],
                'type': 'Estado'
            }
            for coords in STATE_COORDINATES.values()
        ])
        
        fig.add_trace(go.Scattergeo(
            lon=states_df['lon'],
            lat=states_df['lat'],
            text=states_df['name'],
            mode='markers',
            marker=dict(
                size=6,
                color='lightgray',
                opacity=0.6,
                line=dict(width=0.5, color='white')
            ),
            name='Estados',
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=False
        ))
    
    # Añadir rutas si se proporcionan
    if routes_data:
        for route in routes_data:
            add_route_to_map(fig, route)
    
    # Configuración del layout
    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    return fig


def add_route_to_map(fig: go.Figure, route_data: Dict) -> None:
    """
    Añade una ruta al mapa existente
    
    Args:
        fig: Figura de Plotly
        route_data: Diccionario con:
            - origin_state: Estado de origen
            - destination_state: Estado de destino
            - origin_coords: Dict con lat, lon
            - destination_coords: Dict con lat, lon
            - cost: Costo del viaje
            - distance: Distancia en km
            - company: Nombre de la empresa (opcional)
    """
    origin = route_data['origin_coords']
    destination = route_data['destination_coords']
    
    # Línea de la ruta
    fig.add_trace(go.Scattergeo(
        lon=[origin['lon'], destination['lon']],
        lat=[origin['lat'], destination['lat']],
        mode='lines',
        line=dict(width=3, color=COLORS['route']),
        name=f"{route_data.get('origin_state', 'Origen')} → {route_data.get('destination_state', 'Destino')}",
        hovertemplate=f"<b>Ruta</b><br>" +
                     f"Origen: {route_data.get('origin_state', 'N/A')}<br>" +
                     f"Destino: {route_data.get('destination_state', 'N/A')}<br>" +
                     f"Costo: ${route_data.get('cost', 0):,.2f}<br>" +
                     f"Distancia: {route_data.get('distance', 0):.0f} km" +
                     "<extra></extra>"
    ))
    
    # Marcador de origen
    fig.add_trace(go.Scattergeo(
        lon=[origin['lon']],
        lat=[origin['lat']],
        mode='markers+text',
        marker=dict(
            size=15,
            color=COLORS['origin'],
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        text=[route_data.get('origin_state', 'Origen')],
        textposition="top center",
        textfont=dict(size=10, color='#2c3e50'),
        name='Origen',
        hovertemplate=f"<b>Origen</b><br>{route_data.get('origin_state', 'N/A')}<extra></extra>",
        showlegend=False
    ))
    
    # Marcador de destino
    fig.add_trace(go.Scattergeo(
        lon=[destination['lon']],
        lat=[destination['lat']],
        mode='markers+text',
        marker=dict(
            size=15,
            color=COLORS['destination'],
            symbol='square',
            line=dict(width=2, color='white')
        ),
        text=[route_data.get('destination_state', 'Destino')],
        textposition="top center",
        textfont=dict(size=10, color='#2c3e50'),
        name='Destino',
        hovertemplate=f"<b>Destino</b><br>{route_data.get('destination_state', 'N/A')}<extra></extra>",
        showlegend=False
    ))


def create_price_decomposition_chart(components: Dict, chart_type: str = 'pie') -> go.Figure:
    """
    Crea un gráfico de descomposición de precio
    
    Args:
        components: Diccionario con componentes del precio
        chart_type: 'pie' o 'bar'
        
    Returns:
        Figura de Plotly
    """
    labels = list(components.keys())
    values = [comp['valor'] if isinstance(comp, dict) else comp 
              for comp in components.values()]
    
    if chart_type == 'pie':
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(color='white', width=2)
            ),
            textposition='inside',
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>'
        )])
        
        
    
    elif chart_type == 'bar':
        percentages = [(v/sum(values)*100) if isinstance(v, (int, float)) 
                      else (v['valor']/sum([x['valor'] if isinstance(x, dict) else x 
                                           for x in components.values()])*100)
                      for v in components.values()]
        
        fig = go.Figure(data=[go.Bar(
            x=values,
            y=labels,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Viridis',
                line=dict(color='white', width=1.5)
            ),
            text=[f'${v:,.2f} ({p:.1f}%)' for v, p in zip(values, percentages)],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>$%{x:,.2f}<extra></extra>'
        )])
        
        fig.update_layout(
            title='Componentes del Precio',
            xaxis_title='Costo (MXN)',
            yaxis_title='',
            height=400,
            showlegend=False
        )
    
    return fig


def create_comparison_chart(actual_cost: float, predicted_cost: float, 
                           avg_cost: float = None) -> go.Figure:
    """
    Crea un gráfico de comparación de costos
    
    Args:
        actual_cost: Costo real
        predicted_cost: Costo predicho por el modelo
        avg_cost: Costo promedio de la ruta (opcional)
        
    Returns:
        Figura de Plotly
    """
    data = {
        'Tipo': ['Costo Real', 'Predicción ML'],
        'Costo': [actual_cost, predicted_cost],
        'Color': [COLORS['primary'], COLORS['secondary']]
    }
    
    if avg_cost is not None:
        data['Tipo'].append('Promedio Ruta')
        data['Costo'].append(avg_cost)
        data['Color'].append(COLORS['info'])
    
    fig = go.Figure(data=[go.Bar(
        x=data['Tipo'],
        y=data['Costo'],
        marker=dict(
            color=data['Color'],
            line=dict(color='white', width=2)
        ),
        text=[f'${c:,.2f}' for c in data['Costo']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>$%{y:,.2f}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Comparación de Costos',
        yaxis_title='Costo (MXN)',
        xaxis_title='',
        height=400,
        showlegend=False
    )
    
    return fig


def create_feature_importance_chart(importance_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Crea un gráfico de importancia de features
    
    Args:
        importance_df: DataFrame con features e importancia
        top_n: Número de features top a mostrar
        
    Returns:
        Figura de Plotly
    """
    top_features = importance_df.head(top_n)
    
    fig = go.Figure(data=[go.Bar(
        x=top_features['Importance'],
        y=top_features['Feature'],
        orientation='h',
        marker=dict(
            color=top_features['Importance'],
            colorscale='Blues',
            line=dict(color='white', width=1)
        ),
        text=[f'{imp:.3f}' for imp in top_features['Importance']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Importancia: %{x:.4f}<extra></extra>'
    )])
    
    fig.update_layout(
        title=f'Top {top_n} Features Más Importantes',
        xaxis_title='Importancia',
        yaxis_title='',
        height=500,
        showlegend=False
    )
    
    return fig
