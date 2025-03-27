import os
import re


def leer_archivos(carpeta):
    documentos = {}

    for archivo in os.listdir(carpeta):
        match = re.search(r"\d+", archivo)  # Extraer el numero
        doc_id = int(match.group())
        with open(os.path.join(carpeta, archivo), "r", encoding="utf-8") as f:
            documentos[doc_id] = f.read()

    return documentos


def procesar(texto, doc_id):
    texto = texto.lower()  # Convertir a minusculas
    texto = re.sub(r"[^a-z\s]", "", texto)  # Eliminar caracteres especiales
    tokens = texto.split()  # Tokenizar (En este caso separo por espacios)

    global nTokens
    global datos

    nTokens += len(tokens)
    for token in tokens:
        if token not in datos:
            datos[token] = {
                "docsId": [],
                "df": 0,
            }  # Inicializo la estructura de cada termino

        if doc_id not in datos[token]["docsId"]:
            datos[token]["docsId"].append(doc_id)
            datos[token]["df"] = len(datos[token]["docsId"])


def analisis_lexico(carpeta):
    global nDocumentos
    documentos = leer_archivos(carpeta)
    for doc_id, contenido in documentos.items():
        procesar(contenido, doc_id)
        nDocumentos += 1


datos = {}
nTokens = 0
nDocumentos = 0
path = "collection_test/TestCollection"
analisis_lexico(path)
for termino in datos.keys():
    print(termino + " : " + str(datos[termino]["df"]))
print(nDocumentos)
print(nTokens)
print(len(list(datos.keys())))
