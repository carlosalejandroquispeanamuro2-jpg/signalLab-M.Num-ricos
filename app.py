import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, CubicSpline, BarycentricInterpolator
from scipy.optimize import brentq
from scipy.integrate import trapezoid, simpson

st.set_page_config(page_title="SignalLab Numérico", page_icon="📈", layout="wide")
st.title("SignalLab Numérico")
st.write("Analizador de datos numéricos: carga un CSV o Excel con dos columnas numéricas (x e y), "
         "explora interpolación, ajuste polinómico, splines, raíces, integración y derivadas.")

@st.cache_data
def load_file(file_bytes, filename):
    bio = io.BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        # Try common separators/encodings
        try:
            return pd.read_csv(bio)
        except UnicodeDecodeError:
            bio.seek(0)
            return pd.read_csv(bio, encoding="latin-1")
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(bio)
    raise ValueError("Formato no compatible. Usa CSV, XLSX o XLS.")

uploaded = st.file_uploader("Sube tu archivo de datos", type=["csv", "xlsx", "xls"])
if uploaded:
    try:
        raw = load_file(uploaded.getvalue(), uploaded.name)
        st.subheader("Vista previa del archivo")
        st.dataframe(raw.head(20), use_container_width=True)
        numeric_cols = list(raw.select_dtypes(include=np.number).columns)
        if len(numeric_cols) < 2:
            st.error("El archivo debe contener al menos dos columnas numéricas: una para x y otra para y.")
            st.stop()
        c1, c2 = st.columns(2)
        with c1:
            x_col = st.selectbox("Columna independiente (x)", numeric_cols, index=0)
        with c2:
            y_col = st.selectbox("Columna dependiente (y)", numeric_cols, index=1)
        data = raw[[x_col, y_col]].dropna().copy()
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        data = data.groupby(x_col, as_index=False)[y_col].mean().sort_values(x_col)
        x = data[x_col].to_numpy(dtype=float)
        y = data[y_col].to_numpy(dtype=float)
        if len(x) < 2:
            st.error("Se necesitan al menos dos pares de datos válidos.")
            st.stop()
        if len(np.unique(x)) != len(x):
            st.error("Los valores de x deben ser únicos después de agrupar los datos.")
            st.stop()

        st.success(f"Datos listos: {len(x)} pares numéricos.")
        st.dataframe(data, use_container_width=True)

        method = st.selectbox("Método de análisis", [
            "Gráfica y datos",
            "Interpolación de Newton",
            "Interpolación de Lagrange",
            "Método matricial (ajuste polinómico)",
            "Spline cúbico",
            "Búsqueda de raíz aproximada",
            "Integración numérica",
            "Derivada por diferencias centradas"
        ])
        xmin, xmax = float(np.min(x)), float(np.max(x))
        grid = np.linspace(xmin, xmax, 500)

        if method == "Gráfica y datos":
            fig, ax = plt.subplots()
            ax.plot(x, y, "o", label="Datos")
            ax.set(xlabel=x_col, ylabel=y_col, title="Datos cargados")
            ax.grid(True); ax.legend()
            st.pyplot(fig)

        elif method in ("Interpolación de Newton", "Interpolación de Lagrange"):
            max_nodes = min(len(x), 15)
            n_nodes = st.slider("Número de puntos a usar (máximo 15 para reducir oscilaciones)", 2, max_nodes, min(5, max_nodes))
            xx, yy = x[:n_nodes], y[:n_nodes]
            if method == "Interpolación de Lagrange":
                model = BarycentricInterpolator(xx, yy)
                label = "Lagrange"
            else:
                # Divided differences / Newton evaluation
                coef = yy.astype(float).copy()
                for j in range(1, len(coef)):
                    for i in range(len(coef) - 1, j - 1, -1):
                        coef[i] = (coef[i] - coef[i - 1]) / (xx[i] - xx[i - j])
                def model(z):
                    z = np.asarray(z)
                    result = np.zeros_like(z, dtype=float) + coef[-1]
                    for k in range(len(coef)-2, -1, -1):
                        result = result * (z - xx[k]) + coef[k]
                    return result
                label = "Newton"
            fig, ax = plt.subplots()
            ax.plot(x, y, "o", label="Datos originales")
            ax.plot(grid, model(grid), label=label)
            ax.set(xlabel=x_col, ylabel=y_col, title=f"Interpolación de {label}")
            ax.grid(True); ax.legend()
            st.pyplot(fig)
            q = st.number_input("Evaluar en x =", value=float(np.mean(x)))
            st.write(f"**{label}({q:g}) ≈ {float(np.asarray(model(q))):.10g}**")
            st.caption("La interpolación polinómica de muchos puntos puede oscilar; prueba con pocos nodos.")

        elif method == "Método matricial (ajuste polinómico)":
            degree = st.slider("Grado del polinomio", 1, min(10, len(x)-1), min(2, len(x)-1))
            coeff = np.polyfit(x, y, degree)
            pred = np.polyval(coeff, grid)
            rmse = float(np.sqrt(np.mean((y - np.polyval(coeff, x))**2)))
            fig, ax = plt.subplots()
            ax.plot(x, y, "o", label="Datos")
            ax.plot(grid, pred, label=f"Ajuste grado {degree}")
            ax.set(xlabel=x_col, ylabel=y_col, title="Ajuste polinómico por mínimos cuadrados")
            ax.grid(True); ax.legend()
            st.pyplot(fig)
            st.write("Coeficientes (de mayor a menor grado):", coeff)
            st.write(f"Error cuadrático medio de raíz (RMSE): **{rmse:.6g}**")
            st.caption("El ajuste por mínimos cuadrados no tiene que pasar exactamente por todos los puntos.")

        elif method == "Spline cúbico":
            if len(x) < 3:
                st.warning("Se recomiendan al menos 3 puntos para construir el spline cúbico.")
            spline = CubicSpline(x, y, extrapolate=False)
            fig, ax = plt.subplots()
            ax.plot(x, y, "o", label="Datos")
            ax.plot(grid, spline(grid), label="Spline cúbico")
            ax.set(xlabel=x_col, ylabel=y_col, title="Interpolación mediante spline cúbico")
            ax.grid(True); ax.legend()
            st.pyplot(fig)
            q = st.number_input("Evaluar spline en x =", value=float(np.mean(x)))
            if xmin <= q <= xmax:
                st.write(f"**S({q:g}) ≈ {float(spline(q)):.10g}**")
            else:
                st.warning("El punto debe estar dentro del intervalo de los datos.")

        elif method == "Búsqueda de raíz aproximada":
            spline = CubicSpline(x, y, extrapolate=False)
            crossings = []
            for i in range(len(x)-1):
                if y[i] == 0:
                    crossings.append(float(x[i]))
                elif y[i] * y[i+1] < 0:
                    try:
                        crossings.append(float(brentq(lambda z: float(spline(z)), x[i], x[i+1])))
                    except ValueError:
                        pass
            if len(crossings):
                st.write("Raíces aproximadas de la curva interpolada:")
                st.dataframe(pd.DataFrame({"x_raiz": crossings}))
                fig, ax = plt.subplots()
                ax.plot(x, y, "o-", label="Datos")
                ax.axhline(0, linewidth=1)
                for r in crossings: ax.axvline(r, linestyle="--", alpha=.5)
                ax.set(xlabel=x_col, ylabel=y_col, title="Raíces detectadas")
                ax.grid(True); ax.legend()
                st.pyplot(fig)
            else:
                st.info("No se detectó un cambio de signo entre puntos consecutivos. Puede no existir una raíz en el intervalo o puede tocar el eje sin cambiar de signo.")

        elif method == "Integración numérica":
            if len(x) < 2:
                st.error("Se necesitan al menos dos puntos.")
            else:
                trap = float(trapezoid(y, x))
                st.write(f"**Regla compuesta del trapecio:** {trap:.10g}")
                if len(x) >= 3:
                    st.write(f"**Regla compuesta de Simpson 1/3:** {float(simpson(y, x=x)):.10g}")
                else:
                    st.info("Simpson 1/3 requiere al menos 3 puntos.")
                st.caption("Simpson es más apropiado cuando los puntos están espaciados uniformemente; comprueba las condiciones del método antes de interpretar el resultado.")

        elif method == "Derivada por diferencias centradas":
            if len(x) < 3:
                st.error("Se necesitan al menos tres puntos.")
            else:
                dydx = np.gradient(y, x, edge_order=2 if len(x) >= 3 else 1)
                result = pd.DataFrame({x_col: x, y_col: y, "dy_dx_aprox": dydx})
                st.dataframe(result, use_container_width=True)
                fig, ax = plt.subplots()
                ax.plot(x, dydx, "o-", label="Derivada aproximada")
                ax.set(xlabel=x_col, ylabel="dy/dx", title="Tasa de cambio aproximada")
                ax.grid(True); ax.legend()
                st.pyplot(fig)
    except Exception as exc:
        st.error(f"No se pudo procesar el archivo: {exc}")
else:
    st.info("Carga un archivo CSV o Excel para comenzar.")
    st.write("Ejemplo de estructura: dos columnas numéricas, por ejemplo tiempo_s y voltaje_V.")
    st.code("tiempo_s,voltaje_V\n0,0.2\n1,0.8\n2,1.7\n3,2.1\n4,1.4\n5,0.1\n6,-0.4", language="csv")
