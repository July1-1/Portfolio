import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class InteractiveVisualizer:

    def __init__(self, resultados):
        self.resultados = resultados

    # ============================================================
    # TABLA RESUMEN
    # ============================================================
    def tabla_scores(self):
        df = pd.DataFrame({
            "Modelo": list(self.resultados.keys()),
            "R2 Score": [self.resultados[m]["score"] for m in self.resultados]
        })
        return df.sort_values("R2 Score", ascending=False).reset_index(drop=True)

    # ============================================================
    # GRAFICA INTERACTIVA DE R²
    # ============================================================
    def plot_scores(self):
        df = self.tabla_scores()

        fig = px.bar(
            df,
            x="Modelo",
            y="R2 Score",
            title="Comparación de Rendimiento (R²)",
            text="R2 Score",
            color="R2 Score",
            color_continuous_scale="Viridis"
        )
        fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        fig.update_layout(yaxis=dict(range=[0, 1]), height=450)
        fig.show()

    # ============================================================
    # TOP FEATURES GLOBAL (Top-20)
    # ============================================================
    def plot_global_top_features(self):
        registros = []
        for modelo, info in self.resultados.items():
            for feat, val in info["ranking"]:
                registros.append([modelo, feat, val])

        df = pd.DataFrame(registros, columns=["Modelo", "Feature", "Importancia"])
        top = df.sort_values("Importancia", ascending=False).head(20)

        fig = px.bar(
            top,
            x="Importancia",
            y="Feature",
            color="Modelo",
            title="Top 20 Features Globales",
            orientation="h",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=700)
        fig.show()

    # ============================================================
    # HEATMAP DE IMPORTANCIAS
    # ============================================================
    def plot_heatmap(self):
        importancia_total = {}

        for modelo, info in self.resultados.items():
            for feat, val in info["ranking"]:
                if feat not in importancia_total:
                    importancia_total[feat] = {}
                importancia_total[feat][modelo] = val

        df_heatmap = pd.DataFrame(importancia_total).fillna(0)

        fig = px.imshow(
            df_heatmap,
            labels=dict(x="Feature", y="Modelo", color="Importancia"),
            title="Heatmap de Importancias por Modelo",
            aspect="auto",
            color_continuous_scale="Viridis"
        )
        fig.update_layout(height=600)
        fig.show()

    # ============================================================
    # FEATURE MÁS IMPORTANTE DEL MEJOR MODELO
    # ============================================================
    def plot_best_model_top_feature(self):
        df_scores = self.tabla_scores()
        mejor_modelo = df_scores.loc[0, "Modelo"]

        ranking = self.resultados[mejor_modelo]["ranking"]
        feature, importancia = ranking[0]

        print(f"\n🏆 Mejor modelo: {mejor_modelo}")
        print(f"⭐ Feature más importante: {feature} (importancia = {importancia:.4f})")

        fig = px.bar(
            x=[importancia],
            y=[feature],
            orientation="h",
            title=f"Feature Más Importante del Mejor Modelo ({mejor_modelo})",
            labels={"x": "Importancia", "y": "Feature"},
            color=[importancia],
            color_continuous_scale="Viridis"
        )
        fig.update_layout(height=300)
        fig.show()

    # ============================================================
    # MOSTRAR TODO (DASHBOARD INTERACTIVO)
    # ============================================================
    def show(self):
        df_scores = self.tabla_scores()

        print("===== SCORE R² POR MODELO =====")
        print(df_scores.to_string(index=False))

        self.plot_scores()
        self.plot_global_top_features()
        self.plot_heatmap()
        self.plot_best_model_top_feature()
