import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
import matplotlib.pyplot as plt

def plot_anomalies(model, test_data, title, ax):
    # Ordenar por id
    test_data = test_data.sort_values(by='id')

    test_predictions = model.predict(test_data[['dato']])
    anomalies = test_data.loc[test_data['anomalia'] == 1]
    detected_anomalies = test_data.loc[test_predictions == 1]
    undetected_anomalies = anomalies.loc[~anomalies.index.isin(detected_anomalies.index)]

    ax.plot(test_data['id'], test_data['dato'], label='Datos Normales', color='blue', alpha=0.7)
    ax.scatter(detected_anomalies['id'], detected_anomalies['dato'], label='Anomalías Detectadas', color='green', marker='o')
    ax.scatter(undetected_anomalies['id'], undetected_anomalies['dato'], label='Anomalías No Detectadas', color='red', marker='o')

    ax.set_title(title)
    ax.set_xlabel('id')
    ax.set_ylabel('Dato')
    ax.legend()


# Cargar los datos sin nombres de columna
df = pd.read_csv('model compare\\Dust.csv', header=None, names=['id', 'fecha', 'dato'], parse_dates=[1], infer_datetime_format=True)
df_anomalia = pd.read_csv('model compare\\DustAnomalies.csv', header=None, names=['id', 'anomalia'])

# Unir los dos DataFrames en función de la columna 'id'
df_merged = pd.merge(df, df_anomalia, on='id')

# Dividir los datos en entrenamiento (70%) y prueba (30%)
train_data, test_data = train_test_split(df_merged, test_size=0.015, random_state=42)

# Definir una lista de modelos a probar
models = [
    DecisionTreeClassifier(random_state=42),
    RandomForestClassifier(random_state=42),
    SVC(random_state=42),
    # Agrega más modelos si es necesario
]

best_model = None
best_score = 0

# Iterar sobre los modelos
for model in models:
    # Entrenar el modelo
    model.fit(train_data[['dato']], train_data['anomalia'])

    # Predecir en los datos de prueba
    test_predictions = model.predict(test_data[['dato']])

    # Calcular métricas
    precision = precision_score(test_data['anomalia'], test_predictions)
    recall = recall_score(test_data['anomalia'], test_predictions)
    f1 = f1_score(test_data['anomalia'], test_predictions)
    accuracy = accuracy_score(test_data['anomalia'], test_predictions)
    conf_matrix = confusion_matrix(test_data['anomalia'], test_predictions)

    print(f"\nMetrics for model {model.__class__.__name__}:")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1-Score: {f1}")
    print(f"Accuracy: {accuracy}")
    print(f"Confusion matrix:")
    print(conf_matrix)

    # Actualizar el mejor modelo si es necesario
    average_score = (precision + recall + f1 + accuracy) / 4
    if average_score > best_score:
        best_score = average_score
        best_model = model

# Imprimir el mejor modelo
print(f"\nEl mejor modelo es: {best_model.__class__.__name__} con un puntaje promedio de {best_score}")

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
fig.suptitle('Anomalías Detectadas por Modelo')

# Iterar sobre los modelos y generar las gráficas
for model, ax in zip(models, axes.flatten()):
    model.fit(train_data[['dato']], train_data['anomalia'])
    plot_anomalies(model, test_data, model.__class__.__name__, ax)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()
