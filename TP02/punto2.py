import sys
import os
import re


def leer_archivos(carpeta):
    documentos = {}
    doc_id = 0

    for archivo in os.listdir(carpeta):
        with open(os.path.join(carpeta, archivo), "r", encoding="utf-8") as f:
            documentos[doc_id] = f.read()
            doc_id += 1

    return documentos


def leer_vacias(archivo):
    vacias = []
    with open(archivo, "r", encoding="utf-8") as f:
        for line in f:
            vacias.append(line.strip())
    return vacias


def sacar_acentos(texto):
    texto = re.sub(r"[áàäâã]", "a", texto)
    texto = re.sub(r"[éèëê]", "e", texto)
    texto = re.sub(r"[íìïî]", "i", texto)
    texto = re.sub(r"[óòöôõ]", "o", texto)
    texto = re.sub(r"[úùüû]", "u", texto)
    return texto


def procesar(texto, doc_id):
    global datos
    global min
    global max
    global cont

    texto = texto.lower()  # Convertir a minusculas
    texto = sacar_acentos(texto)
    texto = re.sub(r"[^a-z\s]", "", texto)  # Eliminar caracteres especiales
    tokens = texto.split()  # Tokenizar (En este caso separo por espacios)

    if eliminar_vacias:
        global archivo_vacias
        vacias = leer_vacias(archivo_vacias)

    tokens = [
        token
        for token in tokens
        if (min <= len(token) <= max) and (not eliminar_vacias or token not in vacias)
    ]  # Filtro por longitud y no palabra vacia

    cont["n_documentos"] += 1
    cont["n_tokens"] += len(tokens)

    if len(tokens) < cont["n_tokens_shortest"]:
        cont["n_tokens_shortest"] = len(tokens)
        cont["n_terminos_shortest"] = len(set(tokens))  # Elimino duplicados
    if len(tokens) > cont["n_tokens_longest"]:
        cont["n_tokens_longest"] = len(tokens)
        cont["n_terminos_longest"] = len(set(tokens))

    for token in tokens:

        if token not in datos:
            datos[token] = {
                "docsId": [],
                "df": 0,
                "cf": 0,
            }  # Inicializo la estructura de cada termino
            cont["n_terminos"] += 1
            cont["suma_longitudes_terminos"] += len(token)

        if doc_id not in datos[token]["docsId"]:
            datos[token]["docsId"].append(doc_id)
            datos[token]["df"] = len(datos[token]["docsId"])

        datos[token]["cf"] += 1

    return


def get_ranking_frecuencias():
    mayores_10 = {}
    menores_10 = {}
    mayores_10 = dict(
        sorted(datos.items(), key=lambda x: x[1]["cf"], reverse=True)[:10]
    )
    menores_10 = dict(sorted(datos.items(), key=lambda x: x[1]["cf"])[:10])
    return mayores_10, menores_10


def get_terminos_unicos():
    unicos = []
    for termino, contenido in datos.items():
        if contenido["cf"] == 1:
            unicos.append(termino)
    return unicos


def escribir_archivo_terminos():
    with open("terminos.txt", "w", encoding="utf-8") as f:
        f.write("<termino> <CF> <DF>\n")
        for termino, contenido in datos.items():
            linea = f"{termino} {str(contenido['cf'])} {str(contenido['df'])}"
            f.write(linea + "\n")
    return


def escribir_archivo_estadistica():
    with open("estadistica.txt", "w", encoding="utf-8") as f:
        f.write(f"Cantidad de documentos procesados: {str(cont["n_documentos"])}\n")
        f.write(
            f"Cantidad de tokens y términos extraídos: {str(cont["n_tokens"])} {str(cont["n_terminos"])}\n"
        )
        f.write(
            f"Promedio de tokens y términos de los documentos: {str(cont["avg_tokens"])} {str(cont["avg_terminos"])}\n"
        )
        f.write(f"Largo promedio de un término: {str(cont["avg_len_terminos"])}\n")
        f.write(
            f"Cantidad de tokens y términos del documento más corto y del más largo: {str(cont["n_tokens_shortest"])} {str(cont["n_tokens_longest"])} {str(cont["n_terminos_shortest"])} {str(cont["n_terminos_longest"])}\n"
        )
        f.write(
            f"Cantidad de términos que aparecen sólo 1 vez en la colección: {str(cont["terminos_unicos"])}\n"
        )


def escribir_archivo_frecuencias(mayor_10, menor_10):
    with open("frecuencias.txt", "w", encoding="utf-8") as f:
        f.write("10 terminos mas frecuentes\n")
        for termino, valor in mayor_10.items():
            f.write(f"{termino} {valor['cf']}\n")
        f.write("\n10 terminos menos frecuentes\n")
        for termino, valor in menor_10.items():
            f.write(f"{termino} {valor['cf']}\n")


def analisis_lexico(carpeta):
    global datos
    documentos = leer_archivos(carpeta)
    for doc_id, contenido in documentos.items():
        procesar(contenido, doc_id)
    datos = dict(sorted(datos.items()))  # Ordeno alfabeticamente
    return


try:
    directorio = sys.argv[1]
    min = int(sys.argv[2])
    max = int(sys.argv[3])
    eliminar_vacias = False
    if len(sys.argv) == 5:
        archivo_vacias = sys.argv[4]
        eliminar_vacias = True
except IndexError:
    print(
        "USO: python punto2.py <directorio_docs> <min_len> <max_len> (<archivo_vacias>)"
    )
    exit(1)

datos = {}

# Contabilidad
cont = {
    "n_documentos": 0,
    "n_tokens": 0,
    "n_terminos": 0,
    "suma_longitudes_terminos": 0,
    "n_tokens_shortest": float("inf"),
    "n_tokens_longest": 0,
    "n_terminos_shortest": float("inf"),
    "n_terminos_longest": 0,
    "terminos_unicos": 0,
}

analisis_lexico(directorio)

cont["avg_tokens"] = round(cont["n_tokens"] / cont["n_documentos"], 2)
cont["avg_terminos"] = round(cont["n_terminos"] / cont["n_documentos"], 2)
cont["avg_len_terminos"] = round(
    cont["suma_longitudes_terminos"] / cont["n_terminos"], 2
)
cont["terminos_unicos"] = len(get_terminos_unicos())

escribir_archivo_terminos()  # Escribir terminos en archivo terminos.txt

escribir_archivo_estadistica()  # Escribo la contabilidad en estadistica.txt

mayor_10, menor_10 = get_ranking_frecuencias()
escribir_archivo_frecuencias(
    mayor_10, menor_10
)  # Top de terminos de mayor y menor frecuencia en frecuencias.txt
