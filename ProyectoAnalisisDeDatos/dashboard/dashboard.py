"""
Dashboard Principal de Streamlit para Análisis de Rutas de Transporte
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict

from config import DASHBOARD_CONFIG, COLORS
from data_processor import (
    load_data, 
    get_unique_values,
    get_unique_origin_states,
    get_unique_destination_states,
    filter_by_route,
    get_route_summary,
    get_state_coordinates,
    get_available_origins_for_destination,
    get_available_companies_for_route,
    get_unique_transport_types,
    get_available_transport_types_for_route,
    filter_by_transport,
    get_comparative_metrics
)
from ml_models import get_trained_model
from map_utils import (
    create_mexico_map,
    create_price_decomposition_chart,
    create_comparison_chart,
    create_feature_importance_chart
)


# Configuración de la página
st.set_page_config(
    page_title=DASHBOARD_CONFIG['title'],
    page_icon=DASHBOARD_CONFIG['page_icon'],
    layout=DASHBOARD_CONFIG['layout'],
    initial_sidebar_state=DASHBOARD_CONFIG['initial_sidebar_state']
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #3498db;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #3498db;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Función principal del dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header"> Ternium Dashboard de Análisis de Rutas de Transporte</h1>', 
                unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner('Cargando datos'):
        df = load_data()
    
    if df.empty:
        st.error("No se pudieron cargar los datos. Verifica que el archivo 'Viajes_features_clean.csv' existe.")
        st.stop()
    
    # Entrenar/cargar modelos
    predictor = get_trained_model(df)
    
    # ==================== SIDEBAR ====================
    st.sidebar.title("Filtros de Búsqueda")
    
    # Filtro de destino primero
    destinos = ['Todos'] + get_unique_destination_states(df)
    destino_selected = st.sidebar.selectbox(
        "Destino (Estado)",
        destinos,
        help="Selecciona el estado de destino"
    )
    
    # Filtro de origen (dependiente del destino)
    if destino_selected != 'Todos':
        origenes = ['Todos'] + get_available_origins_for_destination(df, destino_selected)
    else:
        origenes = ['Todos'] + get_unique_origin_states(df)
    
    origen_selected = st.sidebar.selectbox(
        "Origen (Estado)",
        origenes,
        help="Selecciona el estado de origen"
    )
    
    # Filtrar dataframe por ruta
    df_filtered = filter_by_route(df, origen_selected, destino_selected)
    
    # Filtro de Tipo de Transporte
    if len(df_filtered) > 0:
        transport_types = ['Todos'] + get_available_transport_types_for_route(
            df, origen_selected, destino_selected
        )
    else:
        transport_types = ['Todos'] + get_unique_transport_types(df)
        
    transport_selected = st.sidebar.selectbox(
        "Tipo de Transporte",
        transport_types,
        help="Selecciona el tipo de transporte"
    )
    
    # Aplicar filtro de transporte
    if transport_selected != 'Todos':
        df_filtered = filter_by_transport(df_filtered, transport_selected)
    
    # Filtro de empresa (dependiente de la ruta y transporte)
    if len(df_filtered) > 0:
        empresas = ['Todas'] + get_available_companies_for_route(
            df, origen_selected, destino_selected
        )
    else:
        empresas = ['Todas']
    
    empresa_selected = st.sidebar.selectbox(
        "Empresa de Transporte",
        empresas,
        help="Selecciona la empresa transportista"
    )
    
    # Aplicar filtro de empresa
    if empresa_selected != 'Todas':
        df_filtered = df_filtered[df_filtered['Nombre'] == empresa_selected]
    
    st.sidebar.divider()
    
    # Información de filtros aplicados
    st.sidebar.info(f"""
    **Viajes filtrados:** {len(df_filtered):,}
    
    **Ruta:** {origen_selected} → {destino_selected}
    
    **Empresa:** {empresa_selected}
    """)
    
    # Opciones de visualización
    st.sidebar.divider()
    st.sidebar.subheader("Opciones de Visualización")
    
    show_map = st.sidebar.checkbox("Mostrar Mapa", value=True)
    show_ml_prediction = st.sidebar.checkbox("Mostrar Predicción ML", value=True)
    show_decomposition = st.sidebar.checkbox("Mostrar Descomposición", value=True)
    show_feature_importance = st.sidebar.checkbox("Importancia de Features", value=True)
    
    model_type = st.sidebar.selectbox(
        "Modelo a Usar",
        ['neural_network', 'random_forest'],
        format_func=lambda x: 'Red Neuronal' if x == 'neural_network' else 'Random Forest'
    )
    
    # ==================== CONTENIDO PRINCIPAL ====================
    
    if len(df_filtered) == 0:
        st.warning("No hay viajes que coincidan con los filtros seleccionados. Intenta con otros criterios.")
        st.stop()
    
    # Obtener resumen de la ruta
    route_summary = get_route_summary(df, origen_selected, destino_selected, empresa_selected)
    
    # ========== SECCIÓN 1: MÉTRICAS CLAVE ==========
    st.subheader("Métricas Clave de la Ruta")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Costo Promedio",
            value=f"${route_summary['costo_promedio']:,.2f}",
            delta=f"Min: ${route_summary['costo_min']:,.0f}"
        )
    
    with col2:
        st.metric(
            label="Distancia",
            value=f"{route_summary['distancia']:.0f} km",
            delta=f"${route_summary['costo_por_km']:.2f}/km" if route_summary['costo_por_km'] > 0 else "N/A"
        )
    
    with col3:
        st.metric(
            label="Tiempo Estimado",
            value=f"{route_summary['tiempo']:.0f} min",
            delta=f"{route_summary['tiempo']/60:.1f} hrs"
        )
    
    with col4:
        st.metric(
            label="Viajes Realizados",
            value=f"{route_summary['num_viajes']:,}",
            delta=f"Max: ${route_summary['costo_max']:,.0f}"
        )
    
    
    # Métricas Comparativas (NUEVO)
    if origen_selected != 'Todos' and destino_selected != 'Todos':
        comp_metrics = get_comparative_metrics(df, origen_selected, destino_selected, transport_selected)
        
        if comp_metrics:
            st.divider()
            st.subheader("Comparativa de Empresas")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            
            with m_col1:
                freq = comp_metrics['most_frequent']
                st.metric(
                    label="Empresa Más Frecuente",
                    value=freq['name'],
                    delta=f"{freq['trips']} viajes | ${freq['avg_cost']:,.0f} prom"
                )
                
            with m_col2:
                cheap = comp_metrics['cheapest']
                st.metric(
                    label="Empresa Más Económica",
                    value=cheap['name'],
                    delta=f"${cheap['avg_cost']:,.0f} costo promedio",
                    delta_color="inverse"
                )
                
            with m_col3:
                savings = comp_metrics['savings']
                st.metric(
                    label="Ahorro Potencial",
                    value=f"${savings['amount']:,.0f}",
                    delta=f"{savings['percentage']:.1f}% de diferencia",
                    delta_color="normal"
                )
    
    st.divider()
    
    # ========== SECCIÓN 2: MAPA Y RUTA ==========
    if show_map and origen_selected != 'Todos' and destino_selected != 'Todos':
        st.subheader("Visualización de Ruta")
        
        # Obtener coordenadas
        origen_coords = get_state_coordinates(origen_selected)
        destino_coords = get_state_coordinates(destino_selected)
        
        if origen_coords and destino_coords:
            route_data = {
                'origin_state': origen_selected,
                'destination_state': destino_selected,
                'origin_coords': origen_coords,
                'destination_coords': destino_coords,
                'cost': route_summary['costo_promedio'],
                'distance': route_summary['distancia'],
                'company': empresa_selected
            }
            
            fig_map = create_mexico_map([route_data], show_all_states=True)
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No se encontraron coordenadas para la ruta seleccionada")
    
    st.divider()
    
    # ========== SECCIÓN 3: PREDICCIÓN ML Y DESCOMPOSICIÓN ==========
    if show_ml_prediction or show_decomposition:
        st.subheader("Análisis con Machine Learning")
        
        # Seleccionar un viaje representativo para análisis
        sample_trip = df_filtered.iloc[0]
        
        tab1, tab2, tab3 = st.tabs(["Predicción ML", "Descomposición de Precio", "Detalle del Viaje"])
        
        with tab1:
            if show_ml_prediction:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Comparación de Costos")
                    
                    actual_cost = sample_trip['Costo']
                    
                    # Nota: La predicción requeriría preparar features del viaje
                    # Por simplicidad, usamos el costo promedio como "predicción"
                    predicted_cost = route_summary['costo_promedio']
                    
                    fig_comparison = create_comparison_chart(
                        actual_cost, 
                        predicted_cost,
                        route_summary['costo_promedio']
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)
                    
                    
                
                with col2:
                    st.markdown("### Información del Modelo")

                    st.info("""
                    El modelo predice el costo basándose en:
                    - Distancia de la ruta
                    - Tiempo estimado de viaje
                    - Peso de la carga
                    - Tipo de transporte utilizado
                    - Empresa transportista
                    """)

                    # Métricas de error
                    error = abs(actual_cost - predicted_cost)
                    error_pct = (error / actual_cost * 100) if actual_cost > 0 else 0
                    
                    st.metric(
                        label="Error Absoluto",
                        value=f"${error:,.2f}",
                        delta=f"{error_pct:.1f}% de error"
                    )
        
        with tab2:
            if show_decomposition:
                st.markdown("### Descomposición del Precio")
                
                # Obtener descomposición
                price_components = predictor.decompose_price(sample_trip, detailed=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de pie
                    fig_pie = create_price_decomposition_chart(price_components, chart_type='pie')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Gráfico de barras
                    fig_bar = create_price_decomposition_chart(price_components, chart_type='bar')
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Tabla de detalle
                st.markdown("#### Detalle de Componentes")
                
                components_df = pd.DataFrame([
                    {
                        'Componente': k,
                        'Valor': f"${v['valor']:,.2f}",
                        'Porcentaje': f"{v['porcentaje']:.1f}%"
                    }
                    for k, v in price_components.items()
                ])
                
                st.dataframe(components_df, use_container_width=True, hide_index=True)
        
        with tab3:
            st.markdown("### Información Detallada del Viaje")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Ruta:** {sample_trip.get('Ori-Dest', 'N/A')}
                
                **Origen:** {sample_trip.get('Origen', 'N/A')}
                
                **Destino:** {sample_trip.get('Destino', 'N/A')}
                
                **Empresa:** {sample_trip.get('Nombre', 'N/A')}
                
                **Tipo de Transporte:** {sample_trip.get('Tipo transporte', 'N/A')}
                """)
            
            with col2:
                st.markdown(f"""
                **Distancia:** {sample_trip.get('Distancia_x', 0):.0f} km
                
                **Tiempo:** {sample_trip.get('Tiempo_x', 0):.0f} min
                
                **Peso Total:** {sample_trip.get('Peso Total (kg)', 0):,.0f} kg
                
                **Costo:** ${sample_trip.get('Costo', 0):,.2f}
                
                **Costo por Tonelada:** ${sample_trip.get('CostoxTn', 0):,.2f}
                """)
    
    st.divider()
    
    # ========== SECCIÓN 4: IMPORTANCIA DE FEATURES ==========
    if show_feature_importance:
        st.subheader("Importancia de Features")
        
        importance_df = predictor.get_feature_importance()
        
        if not importance_df.empty:
            fig_importance = create_feature_importance_chart(importance_df, top_n=15)
            st.plotly_chart(fig_importance, use_container_width=True)
            
            st.info("""
            Esta gráfica muestra qué factores tienen mayor impacto en el costo de transporte.
            Features con mayor importancia son las que más influyen en la predicción del precio.
            """)
        else:
            st.warning("No hay datos de importancia de features disponibles")
    
    st.divider()
    
    # ========== SECCIÓN 5: TABLA DE DATOS ==========
    st.subheader("Datos de Viajes Filtrados")
    
    # Seleccionar columnas relevantes
    display_cols = ['Ori-Dest', 'Origen', 'Destino', 'Nombre', 'Distancia_x', 
                   'Tiempo_x', 'Peso Total (kg)', 'Costo', 'CostoxTn']
    
    display_cols = [col for col in display_cols if col in df_filtered.columns]
    
    st.dataframe(
        df_filtered[display_cols].head(50),
        use_container_width=True,
        hide_index=True
    )
    
    if len(df_filtered) > 50:
        st.info(f"Mostrando los primeros 50 de {len(df_filtered):,} viajes")

if __name__ == "__main__":
    main()
