"""
Configuración del proyecto - Coordenadas de estados y parámetros
"""

# Coordenadas aproximadas de capitales/ciudades principales por estado
STATE_COORDINATES = {
    'aguascalientes': {'lat': 21.8853, 'lon': -102.2916, 'name': 'Aguascalientes'},
    'baja california': {'lat': 32.6245, 'lon': -115.4523, 'name': 'Mexicali'},
    'chiapas': {'lat': 16.7516, 'lon': -93.1029, 'name': 'Tuxtla Gutiérrez'},
    'chihuahua': {'lat': 28.6353, 'lon': -106.0889, 'name': 'Chihuahua'},
    'ciudad de mexico': {'lat': 19.4326, 'lon': -99.1332, 'name': 'CDMX'},
    'coahuila de zaragoza': {'lat': 25.4232, 'lon': -101.0053, 'name': 'Saltillo'},
    'durango': {'lat': 24.0277, 'lon': -104.6532, 'name': 'Durango'},
    'etro guadalajara': {'lat': 20.6597, 'lon': -103.3496, 'name': 'Guadalajara'},
    'metro guadalajara': {'lat': 20.6597, 'lon': -103.3496, 'name': 'Guadalajara'},
    'extranjero laredo tx': {'lat': 27.5306, 'lon': -99.4803, 'name': 'Laredo, TX'},
    'guanajuato': {'lat': 21.0190, 'lon': -101.2574, 'name': 'León'},
    'hidalgo': {'lat': 20.0911, 'lon': -98.7624, 'name': 'Pachuca'},
    'jalisco': {'lat': 20.6597, 'lon': -103.3496, 'name': 'Guadalajara'},
    'michoacan de ocampo': {'lat': 19.7039, 'lon': -101.1844, 'name': 'Morelia'},
    'nuevo leon': {'lat': 25.6866, 'lon': -100.3161, 'name': 'Monterrey'},
    'puebla': {'lat': 19.0414, 'lon': -98.2063, 'name': 'Puebla'},
    'queretaro': {'lat': 20.5888, 'lon': -100.3899, 'name': 'Querétaro'},
    'quintana roo': {'lat': 21.1619, 'lon': -86.8515, 'name': 'Cancún'},
    'riva palacio chi': {'lat': 28.6353, 'lon': -106.0889, 'name': 'Chihuahua'},
    'san jose iturbide': {'lat': 21.0047, 'lon': -100.3897, 'name': 'San José Iturbide'},
    'san luis potosi': {'lat': 22.1565, 'lon': -100.9855, 'name': 'San Luis Potosí'},
    'sinaloa': {'lat': 24.8049, 'lon': -107.3938, 'name': 'Culiacán'},
    'sonora': {'lat': 29.0892, 'lon': -110.9613, 'name': 'Hermosillo'},
    'tamaulipas': {'lat': 23.7369, 'lon': -99.1411, 'name': 'Ciudad Victoria'},
    'tlaxcala': {'lat': 19.3139, 'lon': -98.2404, 'name': 'Tlaxcala'},
    'veracruz de ignacio de la llave': {'lat': 19.1738, 'lon': -96.1342, 'name': 'Veracruz'},
    'yucatan': {'lat': 20.9674, 'lon': -89.5926, 'name': 'Mérida'},
}

# Parámetros de modelos de ML
ML_CONFIG = {
    'neural_network': {
        'hidden_layers': [128, 64, 32],
        'activation': 'relu',
        'epochs': 100,
        'batch_size': 32,
        'learning_rate': 0.001,
        'validation_split': 0.2
    },
    'random_forest': {
        'n_estimators': 200,
        'max_depth': 20,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42
    },
    'test_size': 0.2,
    'random_state': 42
}

# Configuración del dashboard
DASHBOARD_CONFIG = {
    'title': 'Dashboard de Análisis de Rutas de Transporte - Ternium',
    'page_icon': '.',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Colores para visualizaciones
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff9800',
    'info': '#17a2b8',
    'route': '#e74c3c',
    'origin': '#2ecc71',
    'destination': '#3498db'
}

# Componentes de precio para descomposición
PRICE_COMPONENTS = [
    'Costo por Distancia',
    'Costo por Tiempo',
    'Costo por Empresa',
    'Costo por Tipo de Transporte',
    'Costo Base',
    'Otros'
]

# Archivos
DATA_PATH = 'Viajes_features_clean.csv'
MODEL_PATH = 'models/'
CACHE_PATH = 'cache/'
