import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score
from sklearn.inspection import permutation_importance


# ============================================================
# 1. PREPROCESAMIENTO ORIENTADO A OBJETOS
# ============================================================
class DataPreprocessor:

    def __init__(self, test_size=0.2, random_state=42):
        self.test_size = test_size
        self.random_state = random_state

    def preparar(self, df, target):
        X = df.drop(columns=[target])
        y = df[target]

        # One-hot encoding
        X = pd.get_dummies(X, drop_first=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state
        )

        return X_train, X_test, y_train, y_test


# ============================================================
# 2. CLASE PADRE PARA MODELOS
# ============================================================
class BaseModel:

    def train(self, X_train, y_train):
        raise NotImplementedError

    def evaluate(self, X_test, y_test):
        y_pred = self.model.predict(X_test)
        return r2_score(y_test, y_pred)

    def feature_ranking(self, X_train):
        raise NotImplementedError


# ============================================================
# 3. MODELOS INDIVIDUALES
# ============================================================

class LinearModel(BaseModel):
    def __init__(self):
        self.model = LinearRegression()

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def feature_ranking(self, X_train):
        coefs = np.abs(self.model.coef_)
        return sorted(zip(X_train.columns, coefs), key=lambda x: -x[1])


class RidgeModel(BaseModel):
    def __init__(self, alpha=1.0):
        self.model = Ridge(alpha=alpha)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def feature_ranking(self, X_train):
        coefs = np.abs(self.model.coef_)
        return sorted(zip(X_train.columns, coefs), key=lambda x: -x[1])


class RandomForestModel(BaseModel):
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=300, random_state=42)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def feature_ranking(self, X_train):
        importances = self.model.feature_importances_
        return sorted(zip(X_train.columns, importances), key=lambda x: -x[1])


class GradientBoostingModel(BaseModel):
    def __init__(self):
        self.model = GradientBoostingRegressor(random_state=42)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def feature_ranking(self, X_train):
        importances = self.model.feature_importances_
        return sorted(zip(X_train.columns, importances), key=lambda x: -x[1])


# ============================================================
# 4. MLP + SCALER + PERMUTATION IMPORTANCE
# ============================================================
class NeuralNetworkModel(BaseModel):

    def __init__(self, hidden_layers=(64, 32)):
        self.scaler = StandardScaler()
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation="relu",
            max_iter=2000,
            random_state=42
        )

    def train(self, X_train, y_train):
        self.X_train_s = self.scaler.fit_transform(X_train)
        self.model.fit(self.X_train_s, y_train)

    def evaluate(self, X_test, y_test):
        X_test_s = self.scaler.transform(X_test)
        y_pred = self.model.predict(X_test_s)
        return r2_score(y_test, y_pred)

    def feature_ranking(self, X_train):
        X_test_s = self.scaler.transform(X_train)
        perm = permutation_importance(
            self.model, X_test_s, X_train.index, n_repeats=8
        )
        importances = perm.importances_mean
        return sorted(zip(X_train.columns, importances), key=lambda x: -x[1])


# ============================================================
# 5. DEEP SEARCH PARA ENCONTRAR LA MEJOR ARQUITECTURA MLP
# ============================================================
class NeuralDeepSearch:

    def __init__(self, candidate_layers=None):
        if candidate_layers is None:
            self.candidate_layers = [
                (32,), (64,), (128,),
                (64, 32), (128, 64), (256, 128),
                (128, 64, 32), (256, 128, 64)
            ]
        else:
            self.candidate_layers = candidate_layers

    def search(self, X_train, X_test, y_train, y_test):
        best_score = -np.inf
        best_model = None
        best_arch = None

        for arch in self.candidate_layers:
            model = NeuralNetworkModel(hidden_layers=arch)
            model.train(X_train, y_train)
            score = model.evaluate(X_test, y_test)

            print(f"Arquitectura {arch}, Score={score:.4f}")

            if score > best_score:
                best_score = score
                best_arch = arch
                best_model = model

        return best_model, best_arch, best_score


# ============================================================
# 6. ENTRENADOR MAESTRO
# ============================================================
class ModelTrainer:

    def __init__(self):
        self.models = {
            "Regresión Lineal": LinearModel(),
            "Ridge": RidgeModel(),
            "Random Forest": RandomForestModel(),
            "Gradient Boosting": GradientBoostingModel()
        }

    def add_neural_model(self, model):
        self.models["Neural Network"] = model

    def train_all(self, X_train, X_test, y_train, y_test):
        resultados = {}

        for nombre, modelo in self.models.items():
            modelo.train(X_train, y_train)
            score = modelo.evaluate(X_test, y_test)
            ranking = modelo.feature_ranking(X_train)[:10]

            resultados[nombre] = {
                "modelo": modelo,
                "score": score,
                "ranking": ranking
            }

        return resultados


# ============================================================
# 7. USO COMPLETO
# ============================================================
def ejecutar_pipeline(df, target):

    # Preprocesar datos
    pre = DataPreprocessor()
    X_train, X_test, y_train, y_test = pre.preparar(df, target)

    # Deep Search para encontrar la mejor arquitectura de red neuronal
    searcher = NeuralDeepSearch()
    best_nn, arch, score_nn = searcher.search(
        X_train, X_test, y_train, y_test
    )

    print(f"\nMejor arquitectura NN: {arch} con score={score_nn}\n")

    # Entrenar el resto de modelos
    trainer = ModelTrainer()
    trainer.add_neural_model(best_nn)

    resultados = trainer.train_all(X_train, X_test, y_train, y_test)
    return resultados
