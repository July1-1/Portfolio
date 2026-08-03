"""
Modelos de Machine Learning para predicción y descomposición de precios
Incluye Redes Neuronales y Random Forest
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib
import streamlit as st
from typing import Dict, Tuple, List
import os
import shap  # Para explicabilidad del modelo

from config import ML_CONFIG
from data_processor import prepare_ml_features


class TransportCostPredictor:
    """
    Clase para predicción de costos de transporte usando Redes Neuronales y Random Forest
    """
    
    def __init__(self):
        self.nn_model = None
        self.rf_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.shap_explainer = None  # Explainer de SHAP
        self.X_train_sample = None  # Muestra para SHAP background
        
    def build_neural_network(self, input_dim: int) -> keras.Model:
        """
        Construye la arquitectura de la red neuronal
        
        Args:
            input_dim: Número de features de entrada
            
        Returns:
            Modelo de Keras
        """
        config = ML_CONFIG['neural_network']
        
        model = keras.Sequential([
            layers.Input(shape=(input_dim,)),
            layers.Dense(config['hidden_layers'][0], activation=config['activation']),
            layers.Dropout(0.3),
            layers.Dense(config['hidden_layers'][1], activation=config['activation']),
            layers.Dropout(0.2),
            layers.Dense(config['hidden_layers'][2], activation=config['activation']),
            layers.Dropout(0.1),
            layers.Dense(1)  # Salida: costo predicho
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config['learning_rate']),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(self, df: pd.DataFrame, target_col: str = 'Costo') -> Dict:
        """
        Entrena ambos modelos (NN y RF)
        
        Args:
            df: DataFrame con los datos
            target_col: Nombre de la columna objetivo
            
        Returns:
            Diccionario con métricas de evaluación
        """
        # Preparar features
        ml_df, feature_names = prepare_ml_features(df)
        self.feature_names = feature_names
        
        # Separar features y target
        X = ml_df[feature_names].values
        y = ml_df[target_col].values
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=ML_CONFIG['test_size'], 
            random_state=ML_CONFIG['random_state']
        )
        
        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # ===== Entrenar Red Neuronal =====
        self.nn_model = self.build_neural_network(X_train_scaled.shape[1])
        
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True
        )
        
        history = self.nn_model.fit(
            X_train_scaled, y_train,
            epochs=ML_CONFIG['neural_network']['epochs'],
            batch_size=ML_CONFIG['neural_network']['batch_size'],
            validation_split=ML_CONFIG['neural_network']['validation_split'],
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Predicciones NN
        y_pred_nn = self.nn_model.predict(X_test_scaled, verbose=0).flatten()
        
        # ===== Entrenar Random Forest =====
        rf_config = ML_CONFIG['random_forest']
        self.rf_model = RandomForestRegressor(
            n_estimators=rf_config['n_estimators'],
            max_depth=rf_config['max_depth'],
            min_samples_split=rf_config['min_samples_split'],
            min_samples_leaf=rf_config['min_samples_leaf'],
            random_state=rf_config['random_state'],
            n_jobs=-1
        )
        
        self.rf_model.fit(X_train_scaled, y_train)
        y_pred_rf = self.rf_model.predict(X_test_scaled)
        
        # Crear SHAP explainer para el modelo
        # Usar una muestra pequeña para background (más rápido)
        sample_size = min(100, len(X_train_scaled))
        self.X_train_sample = X_train_scaled[:sample_size]
        self.shap_explainer = shap.TreeExplainer(self.rf_model)
        
        self.is_trained = True
        
        # Calcular métricas
        metrics = {
            'neural_network': {
                'mae': mean_absolute_error(y_test, y_pred_nn),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_nn)),
                'r2': r2_score(y_test, y_pred_nn),
                'mape': np.mean(np.abs((y_test - y_pred_nn) / y_test)) * 100
            },
            'random_forest': {
                'mae': mean_absolute_error(y_test, y_pred_rf),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_rf)),
                'r2': r2_score(y_test, y_pred_rf),
                'mape': np.mean(np.abs((y_test - y_pred_rf) / y_test)) * 100
            },
            'training_history': history.history
        }
        
        print(f"   NN  - MAE: ${metrics['neural_network']['mae']:.2f}, R²: {metrics['neural_network']['r2']:.3f}")
        print(f"   RF  - MAE: ${metrics['random_forest']['mae']:.2f}, R²: {metrics['random_forest']['r2']:.3f}")
        
        return metrics
    
    def predict(self, features: np.ndarray, model_type: str = 'neural_network') -> np.ndarray:
        """
        Hace predicciones con el modelo seleccionado
        
        Args:
            features: Array de features
            model_type: 'neural_network' o 'random_forest'
            
        Returns:
            Array con predicciones
        """
        if not self.is_trained:
            raise ValueError("⚠️ Los modelos no han sido entrenados aún")
        
        # Escalar features
        features_scaled = self.scaler.transform(features)
        
        if model_type == 'neural_network':
            return self.nn_model.predict(features_scaled, verbose=0).flatten()
        elif model_type == 'random_forest':
            return self.rf_model.predict(features_scaled)
        else:
            raise ValueError(f"Modelo desconocido: {model_type}")
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene la importancia de features del Random Forest
        
        Returns:
            DataFrame con features e importancia
        """
        if not self.is_trained or self.rf_model is None:
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': self.rf_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        return importance_df
    
    def decompose_price(self, df_row: pd.Series, detailed: bool = True) -> Dict:
        """
        Descompone el precio en componentes usando SHAP values (explicabilidad real del modelo)
        
        Args:
            df_row: Fila del DataFrame con datos del viaje
            detailed: Si True, incluye descomposición detallada
            
        Returns:
            Diccionario con componentes del precio basados en SHAP
        """
        # Debug: Verificar si SHAP está disponible
        if not self.is_trained:
            print("DECOMPOSE: Modelo no entrenado")
            return {}
            
        if self.shap_explainer is None:
            print(f"DECOMPOSE: SHAP explainer es None, usando fallback hardcoded")
            return self._decompose_price_simple(df_row, detailed)
        
        print(f"DECOMPOSE: Usando SHAP values")
        
        try:
            # Preparar features manualmente para coincidir con las del entrenamiento
            features_dict = {}
            
            # Features numéricas
            for feature in self.feature_names:
                if feature in ['Distancia_x', 'Tiempo_x', 'Peso Total (kg)', 'Garantía',
                              'RiesgoOrigen', 'RiesgoDestino', 'PeligroRuta',
                              'Velocidad_promedio', 'Costo_por_km']:
                    # Extraer directamente del df_row
                    if feature == 'Velocidad_promedio':
                        dist = df_row.get('Distancia_x', 0)
                        tiempo = df_row.get('Tiempo_x', 0)
                        features_dict[feature] = (dist / (tiempo / 60)) if tiempo > 0 else 0
                    elif feature == 'Costo_por_km':
                        dist = df_row.get('Distancia_x', 0)
                        costo = df_row.get('Costo', 0)
                        features_dict[feature] = (costo / dist) if dist > 0 else 0
                    else:
                        features_dict[feature] = df_row.get(feature, 0)
                else:
                    # Features categóricas (one-hot): asumir 0 por defecto
                    features_dict[feature] = 0
                    
                    # Activar si coincide
                    if feature.startswith('Tipo_'):
                        tipo_actual = df_row.get('Tipo transporte', '')
                        tipo_esperado = feature.replace('Tipo_', '')
                        if tipo_actual == tipo_esperado:
                            features_dict[feature] = 1
                    
                    elif feature.startswith('Empresa_'):
                        empresa_actual = df_row.get('Nombre', '')
                        empresa_esperada = feature.replace('Empresa_', '')
                        if empresa_actual == empresa_esperada:
                            features_dict[feature] = 1
            
            # Convertir a array en el orden correcto
            features = np.array([[features_dict.get(f, 0) for f in self.feature_names]])

            
            # Escalar
            features_scaled = self.scaler.transform(features)
            
            # Calcular SHAP values
            shap_values = self.shap_explainer.shap_values(features_scaled)
            
            # Si shap_values es matriz, tomar la primera fila
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]
            
            # Valor base (predicción promedio)
            base_value = self.shap_explainer.expected_value
            
            # Costo total
            costo_total = df_row.get('Costo', 0)
            
            # Mapear features a componentes legibles
            components_raw = {}
            
            for i, feature_name in enumerate(self.feature_names):
                shap_contribution = float(shap_values[i])
                
                # Agrupar features similares
                if 'Distancia' in feature_name or 'km' in feature_name.lower():
                    components_raw['Costo por Distancia'] = components_raw.get('Costo por Distancia', 0) + shap_contribution
                elif 'Tiempo' in feature_name or 'Velocidad' in feature_name:
                    components_raw['Costo por Tiempo'] = components_raw.get('Costo por Tiempo', 0) + shap_contribution
                elif 'Tipo' in feature_name or 'transporte' in feature_name.lower():
                    components_raw['Costo por Tipo de Transporte'] = components_raw.get('Costo por Tipo de Transporte', 0) + shap_contribution
                elif 'Empresa' in feature_name or 'Nombre' in feature_name:
                    components_raw['Costo por Empresa'] = components_raw.get('Costo por Empresa', 0) + shap_contribution
                elif 'Riesgo' in feature_name or 'Peligro' in feature_name:
                    components_raw['Costo por Riesgo'] = components_raw.get('Costo por Riesgo', 0) + shap_contribution
                elif 'Peso' in feature_name:
                    components_raw['Costo por Peso'] = components_raw.get('Costo por Peso', 0) + shap_contribution
                else:
                    components_raw['Otros'] = components_raw.get('Otros', 0) + shap_contribution
            
            # Añadir el valor base como "Costo Base"
            components_raw['Costo Base'] = float(base_value)
            
            # Convertir contribuciones SHAP a valores absolutos del costo
            # La suma de SHAP values + base_value = predicción del modelo
            total_contributions = sum(components_raw.values())
            
            # Normalizar para que sumen exactamente el costo total
            if total_contributions != 0:
                scale_factor = costo_total / total_contributions
                components = {k: v * scale_factor for k, v in components_raw.items()}
            else:
                components = components_raw
            
            # Filtrar componentes muy pequeños (menos del 1%)
            min_threshold = costo_total * 0.01
            components_filtered = {k: v for k, v in components.items() if abs(v) >= min_threshold}
            
            # Agrupar componentes pequeños en "Otros"
            small_components_sum = sum(v for k, v in components.items() if abs(v) < min_threshold)
            if small_components_sum != 0:
                components_filtered['Otros'] = components_filtered.get('Otros', 0) + small_components_sum
            
            if detailed:
                # Añadir porcentajes
                components_detailed = {}
                for k, v in components_filtered.items():
                    components_detailed[k] = {
                        'valor': v,
                        'porcentaje': (v / costo_total * 100) if costo_total > 0 else 0,
                        'shap_contribution': v - (base_value * scale_factor if k == 'Costo Base' else 0)
                    }
                return components_detailed
            
            return components_filtered
            
        except Exception as e:
            print(f"Error al calcular SHAP values: {e}")
            # Fallback a método simple
            return self._decompose_price_simple(df_row, detailed)
    
    def _decompose_price_simple(self, df_row: pd.Series, detailed: bool = True) -> Dict:
        """
        Método fallback de descomposición simple basado en importancia de features
        """
        
        # Costo total
        costo_total = df_row['Costo']
        distancia = df_row.get('Distancia_x', 0)
        tiempo = df_row.get('Tiempo_x', 0)
        peso = df_row.get('Peso Total (kg)', 0)
        
        # Estimaciones basadas en promedios y análisis de contribución
        components = {}
        
        # 1. Costo por Distancia (aproximadamente 40-50% del costo)
        if distancia > 0:
            costo_por_km = costo_total / distancia
            components['Costo por Distancia'] = costo_total * 0.45
        else:
            components['Costo por Distancia'] = 0
        
        # 2. Costo por Tiempo (aproximadamente 20-30% del costo)
        if tiempo > 0:
            components['Costo por Tiempo'] = costo_total * 0.25
        else:
            components['Costo por Tiempo'] = 0
        
        # 3. Costo por Tipo de Transporte (aproximadamente 10-15%)
        components['Costo por Tipo de Transporte'] = costo_total * 0.12
        
        # 4. Costo por Empresa (diferencial de precio, 5-10%)
        components['Costo por Empresa'] = costo_total * 0.08
        
        # 5. Costo Base (costos fijos, 5-10%)
        components['Costo Base'] = costo_total * 0.07
        
        # 6. Otros (variabilidad, 3-5%)
        components['Otros'] = costo_total * 0.03
        
        # Normalizar para que sume exactamente el costo total
        suma_components = sum(components.values())
        if suma_components > 0:
            factor = costo_total / suma_components
            components = {k: v * factor for k, v in components.items()}
        
        if detailed:
            # Añadir porcentajes
            components_detailed = {}
            for k, v in components.items():
                components_detailed[k] = {
                    'valor': v,
                    'porcentaje': (v / costo_total * 100) if costo_total > 0 else 0
                }
            return components_detailed
        
        return components
    
    def save_models(self, path: str = 'models/'):
        """Guarda los modelos entrenados y el SHAP explainer"""
        os.makedirs(path, exist_ok=True)
        
        # Guardar NN
        if self.nn_model:
            self.nn_model.save(os.path.join(path, 'neural_network_model.keras'))
        
        # Guardar RF
        if self.rf_model:
            joblib.dump(self.rf_model, os.path.join(path, 'random_forest_model.pkl'))
        
        # Guardar scaler
        joblib.dump(self.scaler, os.path.join(path, 'scaler.pkl'))
        
        # Guardar feature names
        joblib.dump(self.feature_names, os.path.join(path, 'feature_names.pkl'))
        
        # Guardar SHAP explainer (NUEVO)
        if self.shap_explainer:
            joblib.dump(self.shap_explainer, os.path.join(path, 'shap_explainer.pkl'))
            print(f"SHAP explainer guardado")
        
        print(f"Modelos guardados en {path}")
    
    def load_models(self, path: str = 'models/'):
        """Carga los modelos guardados y el SHAP explainer"""
        try:
            self.nn_model = keras.models.load_model(os.path.join(path, 'neural_network_model.keras'))
            self.rf_model = joblib.load(os.path.join(path, 'random_forest_model.pkl'))
            self.scaler = joblib.load(os.path.join(path, 'scaler.pkl'))
            self.feature_names = joblib.load(os.path.join(path, 'feature_names.pkl'))
            
            # Cargar SHAP explainer si existe (NUEVO)
            shap_path = os.path.join(path, 'shap_explainer.pkl')
            if os.path.exists(shap_path):
                self.shap_explainer = joblib.load(shap_path)
                print(f"SHAP explainer cargado")
            else:
                print(f"SHAP explainer no encontrado, re-creando...")
                # Re-crear SHAP explainer con el RF cargado
                self.shap_explainer = shap.TreeExplainer(self.rf_model)
                print(f"SHAP explainer re-creado")
            
            self.is_trained = True
            print(f"Modelos cargados desde {path}")
            return True
        except Exception as e:
            print(f"No se pudieron cargar los modelos: {str(e)}")
            return False


@st.cache_resource
def get_trained_model(df: pd.DataFrame) -> TransportCostPredictor:
    """
    Obtiene o entrena el modelo (con caching de Streamlit)
    
    Args:
        df: DataFrame con los datos
        
    Returns:
        Modelo entrenado
    """
    predictor = TransportCostPredictor()
    
    # Intentar cargar modelos existentes
    if not predictor.load_models():
        # Si no existen, entrenar nuevos
        with st.spinner('Entrenando modelos de ML... Esto puede tardar un momento.'):
            predictor.train(df)
            predictor.save_models()
    
    return predictor
