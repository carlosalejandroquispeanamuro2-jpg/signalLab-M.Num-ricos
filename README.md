# SignalLab Numérico

Aplicación web académica para analizar archivos de datos numéricos mediante métodos numéricos.

## ¿Qué hace?
- Carga archivos CSV, XLSX y XLS.
- Permite elegir las columnas numéricas `x` e `y`.
- Grafica los datos.
- Interpolación de Newton y Lagrange.
- Ajuste polinómico por mínimos cuadrados (formulación matricial).
- Spline cúbico.
- Detección de raíces aproximadas de la curva interpolada.
- Integración compuesta por trapecios y Simpson 1/3.
- Aproximación de derivadas con diferencias finitas.

## Requisitos
Python 3.10 o posterior recomendado.

## Instalación local
```bash
python -m venv .venv
```
Activar entorno:
- Windows: `.venv\Scripts\activate`
- Linux/macOS: `source .venv/bin/activate`

Instalar dependencias:
```bash
pip install -r requirements.txt
```

Ejecutar:
```bash
streamlit run app.py
```
Se abrirá una dirección local en el navegador.

## Formato del archivo
El archivo debe ser CSV o Excel y contener al menos dos columnas numéricas: una variable independiente (x) y una dependiente (y). Por ejemplo, tiempo y voltaje. No significa que pueda leer cualquier archivo sin estructura; necesita datos tabulares numéricos.

## Publicación
Sube `app.py`, `requirements.txt`, `README.md` y `datos_ejemplo.csv` a un repositorio público en GitHub. Para compartir la aplicación interactiva, puedes desplegarla en Streamlit Community Cloud conectando ese repositorio y seleccionando `app.py`.

## Limitaciones académicas
- El ajuste matricial se realiza por mínimos cuadrados mediante `numpy.polyfit`.
- La búsqueda de raíces detecta cruces de cero entre puntos consecutivos y refina la raíz usando un spline cúbico; no garantiza detectar raíces tangenciales.
- La interpolación de alto grado puede presentar oscilaciones.
- Simpson requiere condiciones apropiadas sobre la cantidad y distribución de los datos.
