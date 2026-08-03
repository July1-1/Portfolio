"""
Procesador de datos para el dashboard de rutas de transporte
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import streamlit as st
from config import STATE_COORDINATES, DATA_PATH


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Carga y prepara los datos del CSV
    
    Returns:
        DataFrame con los datos limpios
    """
    try:
        df = pd.read_csv(DATA_PATH)
        
        # Convertir nombres de estados a minúsculas para matching
        if 'OrigenEstado' in df.columns:
            df['OrigenEstado'] = df['OrigenEstado'].str.lower().str.strip()
        if 'DestinoEstado' in df.columns:
            df['DestinoEstado'] = df['DestinoEstado'].str.lower().str.strip()
            
        # Convertir columnas numéricas
        numeric_cols = ['Costo', 'Distancia_x', 'Tiempo_x', 'Peso Total (kg)', 
                       'CostoxTn', 'Monto Real', 'Monto Falso', 'Monto Reparto']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Eliminar filas con valores nulos críticos
        df = df.dropna(subset=['Costo', 'Origen', 'Destino'])
        
        return df
    
    except FileNotFoundError:
        st.error(f"❌ No se encontró el archivo {DATA_PATH}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame()


def get_unique_values(df: pd.DataFrame, column: str) -> List[str]:
    """
    Obtiene valores únicos de una columna
    
    Args:
        df: DataFrame
        column: Nombre de la columna
        
    Returns:
        Lista de valores únicos ordenados
    """
    if column in df.columns:
        return sorted(df[column].dropna().unique().tolist())
    return []


def get_unique_routes(df: pd.DataFrame) -> List[str]:
    """
    Obtiene rutas únicas (Ori-Dest)
    
    Args:
        df: DataFrame
        
    Returns:
        Lista de rutas únicas
    """
    return get_unique_values(df, 'Ori-Dest')


def get_unique_origin_states(df: pd.DataFrame) -> List[str]:
    """
    Obtiene estados de origen únicos
    
    Args:
        df: DataFrame
        
    Returns:
        Lista de estados de origen únicos
    """
    return get_unique_values(df, 'OrigenEstado')


def get_unique_destination_states(df: pd.DataFrame) -> List[str]:
    """
    Obtiene estados de destino únicos
    
    Args:
        df: DataFrame
        
    Returns:
        Lista de estados de destino únicos
    """
    return get_unique_values(df, 'DestinoEstado')


def get_unique_companies(df: pd.DataFrame) -> List[str]:
    """
    Obtiene empresas de transporte únicas
    
    Args:
        df: DataFrame
        
    Returns:
        Lista de empresas únicas
    """
    return get_unique_values(df, 'Nombre')


def get_unique_transport_types(df: pd.DataFrame) -> List[str]:
    """
    Obtiene tipos de transporte únicos
    
    Args:
        df: DataFrame
        
    Returns:
        Lista de tipos de transporte únicos
    """
    return get_unique_values(df, 'Tipo transporte')


def get_state_coordinates(state_name: str) -> Optional[Dict[str, float]]:
    """
    Obtiene las coordenadas de un estado
    
    Args:
        state_name: Nombre del estado (case insensitive)
        
    Returns:
        Diccionario con lat, lon y name, o None si no se encuentra
    """
    state_key = state_name.lower().strip()
    return STATE_COORDINATES.get(state_key)


def filter_by_route(df: pd.DataFrame, origin: str = None, 
                   destination: str = None) -> pd.DataFrame:
    """
    Filtra el DataFrame por origen y/o destino (usando OrigenEstado y DestinoEstado)
    
    Args:
        df: DataFrame
        origin: Estado de origen
        destination: Estado de destino
        
    Returns:
        DataFrame filtrado
    """
    filtered_df = df.copy()
    
    if origin and origin != 'Todos':
        filtered_df = filtered_df[filtered_df['OrigenEstado'] == origin]
    
    if destination and destination != 'Todos':
        filtered_df = filtered_df[filtered_df['DestinoEstado'] == destination]
    
    return filtered_df


def filter_by_company(df: pd.DataFrame, company: str = None) -> pd.DataFrame:
    """
    Filtra el DataFrame por empresa
    
    Args:
        df: DataFrame
        company: Nombre de la empresa
        
    Returns:
        DataFrame filtrado
    """
    if company and company != 'Todas':
        return df[df['Nombre'] == company]
    return df


def filter_by_transport(df: pd.DataFrame, transport_type: str = None) -> pd.DataFrame:
    """
    Filtra el DataFrame por tipo de transporte
    
    Args:
        df: DataFrame
        transport_type: Tipo de transporte
        
    Returns:
        DataFrame filtrado
    """
    if transport_type and transport_type != 'Todos':
        return df[df['Tipo transporte'] == transport_type]
    return df


def get_route_summary(df: pd.DataFrame, origin: str, destination: str, 
                     company: str = None) -> Dict:
    """
    Obtiene un resumen de la ruta seleccionada
    
    Args:
        df: DataFrame
        origin: Origen
        destination: Destino
        company: Empresa (opcional)
        
    Returns:
        Diccionario con estadísticas de la ruta
    """
    filtered_df = filter_by_route(df, origin, destination)
    
    if company and company != 'Todas':
        filtered_df = filter_by_company(filtered_df, company)
    
    if len(filtered_df) == 0:
        return {
            'num_viajes': 0,
            'costo_promedio': 0,
            'costo_min': 0,
            'costo_max': 0,
            'distancia': 0,
            'tiempo': 0,
            'peso_promedio': 0
        }
    
    return {
        'num_viajes': len(filtered_df),
        'costo_promedio': filtered_df['Costo'].mean(),
        'costo_min': filtered_df['Costo'].min(),
        'costo_max': filtered_df['Costo'].max(),
        'distancia': filtered_df['Distancia_x'].mean() if 'Distancia_x' in filtered_df.columns else 0,
        'tiempo': filtered_df['Tiempo_x'].mean() if 'Tiempo_x' in filtered_df.columns else 0,
        'peso_promedio': filtered_df['Peso Total (kg)'].mean() if 'Peso Total (kg)' in filtered_df.columns else 0,
        'costo_por_km': (filtered_df['Costo'].mean() / filtered_df['Distancia_x'].mean()) 
                        if 'Distancia_x' in filtered_df.columns and filtered_df['Distancia_x'].mean() > 0 else 0,
        'costo_por_tonelada': filtered_df['CostoxTn'].mean() if 'CostoxTn' in filtered_df.columns else 0
    }


def get_comparative_metrics(df: pd.DataFrame, origin: str, destination: str, 
                           transport_type: str = None) -> Dict:
    """
    Calcula métricas comparativas entre empresas para una ruta
    
    Args:
        df: DataFrame
        origin: Origen
        destination: Destino
        transport_type: Tipo de transporte (opcional)
        
    Returns:
        Diccionario con métricas comparativas
    """
    # Filtrar por ruta y tipo de transporte (IGNORANDO filtro de empresa)
    filtered_df = filter_by_route(df, origin, destination)
    
    if transport_type and transport_type != 'Todos':
        filtered_df = filter_by_transport(filtered_df, transport_type)
    
    if len(filtered_df) == 0:
        return {}
    
    # 1. Empresa más frecuente
    top_company_name = filtered_df['Nombre'].mode().iloc[0]
    top_company_df = filtered_df[filtered_df['Nombre'] == top_company_name]
    top_company_avg_cost = top_company_df['Costo'].mean()
    top_company_trips = len(top_company_df)
    
    # 2. Empresa más barata (promedio)
    avg_costs = filtered_df.groupby('Nombre')['Costo'].mean().sort_values()
    cheapest_company_name = avg_costs.index[0]
    cheapest_company_avg_cost = avg_costs.iloc[0]
    
    # 3. Diferencia y Ahorro
    # Diferencia entre la más frecuente y la más barata
    savings = top_company_avg_cost - cheapest_company_avg_cost
    savings_pct = (savings / top_company_avg_cost * 100) if top_company_avg_cost > 0 else 0
    
    return {
        'most_frequent': {
            'name': top_company_name,
            'avg_cost': top_company_avg_cost,
            'trips': top_company_trips
        },
        'cheapest': {
            'name': cheapest_company_name,
            'avg_cost': cheapest_company_avg_cost
        },
        'savings': {
            'amount': savings,
            'percentage': savings_pct
        }
    }


def prepare_ml_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepara features para modelos de ML
    
    Args:
        df: DataFrame original
        
    Returns:
        Tuple de (DataFrame con features, lista de nombres de features)
    """
    ml_df = df.copy()
    
    # Features numéricas directas
    numeric_features = []
    
    if 'Distancia_x' in ml_df.columns:
        numeric_features.append('Distancia_x')
    if 'Tiempo_x' in ml_df.columns:
        numeric_features.append('Tiempo_x')
    if 'Peso Total (kg)' in ml_df.columns:
        numeric_features.append('Peso Total (kg)')
    if 'Garantía' in ml_df.columns:
        numeric_features.append('Garantía')
    
    # Features de riesgo (NUEVO)
    if 'RiesgoOrigen' in ml_df.columns:
        numeric_features.append('RiesgoOrigen')
    if 'RiesgoDestino' in ml_df.columns:
        numeric_features.append('RiesgoDestino')
    if 'PeligroRuta' in ml_df.columns:
        numeric_features.append('PeligroRuta')
    
    # Features categóricas - One-hot encoding
    categorical_features = []
    
    if 'Tipo transporte' in ml_df.columns:
        tipo_dummies = pd.get_dummies(ml_df['Tipo transporte'], prefix='Tipo')
        ml_df = pd.concat([ml_df, tipo_dummies], axis=1)
        categorical_features.extend(tipo_dummies.columns.tolist())
    
    if 'Nombre' in ml_df.columns:
        # Limitar a las empresas más comunes para evitar demasiadas features
        top_companies = ml_df['Nombre'].value_counts().head(20).index
        ml_df['Nombre_top'] = ml_df['Nombre'].apply(
            lambda x: x if x in top_companies else 'Otras'
        )
        empresa_dummies = pd.get_dummies(ml_df['Nombre_top'], prefix='Empresa')
        ml_df = pd.concat([ml_df, empresa_dummies], axis=1)
        categorical_features.extend(empresa_dummies.columns.tolist())
    
    # Features derivadas
    if 'Distancia_x' in ml_df.columns and 'Tiempo_x' in ml_df.columns:
        ml_df['Velocidad_promedio'] = ml_df['Distancia_x'] / (ml_df['Tiempo_x'] / 60)
        numeric_features.append('Velocidad_promedio')
    
    if 'Costo' in ml_df.columns and 'Distancia_x' in ml_df.columns:
        ml_df['Costo_por_km'] = ml_df['Costo'] / ml_df['Distancia_x']
        numeric_features.append('Costo_por_km')
    
    all_features = numeric_features + categorical_features
    
    # Eliminar NaN en features
    ml_df[all_features] = ml_df[all_features].fillna(0)
    
    return ml_df, all_features


def get_available_origins_for_destination(df: pd.DataFrame, destination: str) -> List[str]:
    """
    Obtiene orígenes disponibles para un destino específico
    
    Args:
        df: DataFrame
        destination: Destino seleccionado
        
    Returns:
        Lista de orígenes disponibles
    """
    if destination == 'Todos':
        return get_unique_values(df, 'OrigenEstado')
    
    filtered_df = df[df['DestinoEstado'] == destination]
    return sorted(filtered_df['OrigenEstado'].dropna().unique().tolist())


def get_available_companies_for_route(df: pd.DataFrame, origin: str, 
                                     destination: str) -> List[str]:
    """
    Obtiene empresas disponibles para una ruta específica
    
    Args:
        df: DataFrame
        origin: Origen
        destination: Destino
        
    Returns:
        Lista de empresas disponibles
    """
    filtered_df = filter_by_route(df, origin, destination)
    return sorted(filtered_df['Nombre'].dropna().unique().tolist())


def get_available_transport_types_for_route(df: pd.DataFrame, origin: str, 
                                           destination: str) -> List[str]:
    """
    Obtiene tipos de transporte disponibles para una ruta específica
    
    Args:
        df: DataFrame
        origin: Origen
        destination: Destino
        
    Returns:
        Lista de tipos de transporte disponibles
    """
    filtered_df = filter_by_route(df, origin, destination)
    return sorted(filtered_df['Tipo transporte'].dropna().unique().tolist())
