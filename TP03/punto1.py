import os
import numpy as np
import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd


def leer_archivos(carpeta):
    documentos = {}
    for archivo in os.listdir(carpeta):
        ruta = os.path.join(carpeta, archivo)
        if os.path.isfile(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                documentos[archivo] = f.read()
    return documentos


def tokenizar(texto):
    tokens = word_tokenize(texto.lower())
    tokens = [t for t in tokens if t not in string.punctuation]
    tokens = [t for t in tokens if t not in stopwords.words("spanish")]
    return tokens


def construir_matriz_termino_documento(documentos):
    tokens_por_doc = {}
    for nombre, texto in documentos.items():
        tokens_por_doc[nombre] = tokenizar(texto)

    terminos = set()
    for tokens in tokens_por_doc.values():
        terminos.update(tokens)

    terminos = sorted(list(terminos))

    # Inicializar matriz con etiquetas
    n_filas = len(terminos) + 1
    n_columnas = len(documentos) + 1
    matriz = np.zeros((n_filas, n_columnas), dtype=object)

    matriz[0, 0] = ""
    for j, nombre_doc in enumerate(documentos.keys()):
        matriz[0, j + 1] = nombre_doc  # Nombres de documentos como columnas

    for i, termino in enumerate(terminos):
        matriz[i + 1, 0] = termino  # Terminos como filas
        for j, nombre_doc in enumerate(documentos.keys()):
            matriz[i + 1, j + 1] = tokens_por_doc[nombre_doc].count(termino)

    return matriz


PATH = "docs-p1"
nltk.download("punkt")
nltk.download("stopwords")
documentos = leer_archivos(PATH)
matriz = construir_matriz_termino_documento(documentos)

# Exportar a CSV usando pandas
# Extraer etiquetas de filas y columnas
columnas = matriz[0, 1:]  # nombres de documentos
filas = matriz[1:, 0]  # términos
datos = matriz[1:, 1:]  # la matriz sin etiquetas

# Crear el DataFrame
df = pd.DataFrame(data=datos, index=filas, columns=columnas)

# Exportar a CSV
df.to_csv("matriz_termino_documento.csv", encoding="utf-8")

# (Opcional) Mostrar por consola con formato
for fila in matriz:
    fila_formateada = [f"{x:<{20}}" for x in fila]
    print("".join(fila_formateada))
