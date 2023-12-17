from flask import Flask, render_template, request, redirect, url_for 
import matplotlib.pyplot as plt
import json
import requests
import psycopg2
import plotly.express as px
import plotly.offline as opy
import pandas as pd 


app = Flask(__name__)


# URL prediction's service
scoring_uri_air = 'http://eb43ed3f-7ca1-4be9-9e49-d08f52425abf.francecentral.azurecontainer.io/score'
scoring_uri_back = 'http://82dc32d0-e323-4cf6-ae96-b32b892c9e2b.francecentral.azurecontainer.io/score'

# Authentication keys
key_air = 'p2xhqZi2C3ht0qSdeYwph4NTCCiUziBx'
key_back = 'Tlj5Tar7gPGdBpVM6rX8p6eNHZdQqfzG'

# Users and password (for demo)
usuarios = {
    'usuario1': 'contrasena1',
    'usuario2': 'contrasena2',
    'a':'a',
    'alejandro':'a',
    'jorge':'a',
    'daniel':'a'
}

# database connection data
host = "database-mine.postgres.database.azure.com"
dbname = "postgres"
user = "user_admin"
password = "contrasenia_1"
sslmode = "require"

# Construct connection string
conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)

# Function to connect with database
def conectar_bd():
    conn = psycopg2.connect(conn_string)
    return conn

# Functions to get data from the forms
def obtener_valores_air_overpressure(formulario):
    valores = [
        float(formulario['valor1']),
        float(formulario['valor2']),
        float(formulario['valor3']),
        float(formulario['valor4']),
        float(formulario['valor5']),
        float(formulario['valor6']),
        float(formulario['valor7']),
        float(formulario['valor8'])
    ]
    return valores

def obtener_valores_backbreak(formulario):
    valores = [
        float(formulario['valor1']),
        float(formulario['valor2']),
        float(formulario['valor3']),
        float(formulario['valor4']),
        float(formulario['valor5']),
        float(formulario['valor6']),
        float(formulario['valor7']),
        float(formulario['valor8'])
    ]
    return valores

# Function to make login on the app
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario in usuarios and usuarios[usuario] == contrasena:
             # Successful login, redirect to the main menu
            return redirect(url_for('menu_principal', usuario=usuario))
        else:
            # Incorrect credentials, show error message
            mensaje_error = 'Incorrect credentials. Try again.'
            return render_template('login.html', mensaje_error=mensaje_error)
     # If it's a GET request or if there's an error, show the login form
    return render_template('login.html', mensaje_error=None)

# Main Menu
@app.route('/menu/<usuario>')
def menu_principal(usuario):
    return render_template('menu.html', usuario=usuario)

# Function to the option of visualizing the variables
@app.route('/visualizar_variables')
def visualizar_variables():
    # Logic for the view variables page
    conn = conectar_bd()
    cursor = conn.cursor()

     # Query to get the last 15 samples from the 'gas' table
    query_gas = '''SELECT time, nitrogensensor, oxygensensor, nitrousgassensor, carbonmonoxidesensor, carbonanididesensor, 
                    sulphurousanididesensor, firedampgassensor, hydrosulphursensor FROM gas ORDER BY time DESC LIMIT 15;'''
    cursor.execute(query_gas)
    resultados_recientes_gas = cursor.fetchall()

    # Query to get the last 15 samples from the 'dust' table
    cursor.execute("SELECT time, concentration FROM dust ORDER BY time DESC LIMIT 15;")
    resultados_recientes_dust = cursor.fetchall()

    # Convert results to pandas DataFrames
    columnas_gas = ['time', 'nitrogensensor', 'oxygensensor', 'nitrousgassensor', 'carbonmonoxidesensor', 'carbonanididesensor', 'sulphurousanididesensor', 'firedampgassensor', 'hydrosulphursensor']
    df_gas = pd.DataFrame(resultados_recientes_gas, columns=columnas_gas)

    columnas_dust = ['time', 'concentration']
    df_dust = pd.DataFrame(resultados_recientes_dust, columns=columnas_dust)

    # Create gas plot with Plotly
    fig_gas = px.line(df_gas, x='time', y=df_gas.columns[1:], title='Last 15 samples of gas')

   # Create dust concentration plot with Plotly
    fig_dust = px.line(df_dust, x='time', y='concentration', title='Last 15 samples of dust concentration')

    # Convert plots to HTML
    plot_html_gas = opy.plot(fig_gas, auto_open=False, output_type='div')
    plot_html_dust = opy.plot(fig_dust, auto_open=False, output_type='div')

     # Clean up and close the database connection
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('visualize_variables.html', plot_html_gas=plot_html_gas, plot_html_dust=plot_html_dust)

# Function to check the kpis
@app.route('/comprobar_kpis')
def comprobar_kpis():
     # Logic for the check KPIs page
    return render_template('check_kpis.html')

# Function to choose which prediction to make
@app.route('/predicciones', methods=['GET', 'POST'])
def predicciones():
    if request.method == 'POST':
        opcion = request.form['opcion']

        if opcion == 'air-overpressure':
            return render_template('form_prediction_air.html')
        elif opcion == 'backbreak':
            return render_template('form_prediction_back.html')
    
    return render_template('selection_prediction.html')

# Function to make the prediciton
@app.route('/realizar_prediccion', methods=['POST'])
def realizar_prediccion():
   # Check if the 'option' key is present in the form
    if 'opcion' not in request.form:
        return 'Opción de predicción no válida'
    opcion = request.form['opcion']
    if opcion == 'air-overpressure':
        valores = obtener_valores_air_overpressure(request.form)
        uri = scoring_uri_air
        key = key_air
    elif opcion == 'backbreak':
        valores = obtener_valores_backbreak(request.form)
        uri = scoring_uri_back
        key = key_back
    else:
        return 'Opción de predicción no válida'

    # Rest of the prediction logic

    data = {"data": [valores]}
    input_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}

    if key:
        headers['Authorization'] = f'Bearer {key}'

    resp = requests.post(uri, input_data, headers=headers)
    respuesta = resp.text

    return render_template('answer_prediction.html', respuesta=respuesta)

# Function to see the kpis mean
@app.route('/visualizar_media_kpi')
def visualizar_media_kpi():
   # Logic to get the mean of KPIs and pass it to the template
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT AVG(precision), AVG(recall), AVG(f1_score), AVG(accuracy) FROM kpi;")
    media_valores = cursor.fetchone()

    # Clean up
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('visualize_mean_kpi.html', media_valores=media_valores)

# Function to visualize last kpi sample
@app.route('/visualizar_ultimo_registro')
def visualizar_ultimo_registro():
   # Logic to get the last record from the table and pass it to the template

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM kpi LIMIT 1;")
    ultimo_resultado = cursor.fetchone()

    # Clean up
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('visualize_last_register.html', ultimo_resultado=ultimo_resultado)


if __name__ == '__main__':
    app.run(debug=True, port=5000)