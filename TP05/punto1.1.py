import os
import json
import sys
import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict


def extraer_texto_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def tokenizar(texto):
    global stop_words
    tokens = word_tokenize(texto.lower())
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    return tokens


def procesar_y_volcar_indice(
    ruta_corpus, n, carpeta_salida, frecuencias, ruta_mapeo="doc_ids.json"
):
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    doc_map = {}  # Mapa para almacenar el mapeo del doc_id a nombre de archivo
    doc_id = 0
    bloque_id = 0

    if frecuencias:
        # Diccionario: termino -> lista de [doc_id, freq]
        indice_parcial = defaultdict(list)
    else:
        # Diccionario: termino -> lista de doc_id
        indice_parcial = defaultdict(list)

    for root, _, files in os.walk(ruta_corpus):
        for archivo in files:
            if archivo.endswith(".html"):
                ruta_completa = os.path.join(root, archivo)
                with open(ruta_completa, encoding="utf-8") as f:
                    html = f.read()
                    texto = extraer_texto_html(html)
                    tokens = tokenizar(texto)

                    # Guardar el mapeo del doc_id al nombre del archivo
                    doc_map[str(doc_id)] = archivo

                    if frecuencias:
                        freqs = defaultdict(int)
                        for token in tokens:
                            freqs[token] += 1
                        for termino, freq in freqs.items():
                            indice_parcial[termino].append([doc_id, freq])
                    else:
                        terminos = set(tokens)
                        for termino in terminos:
                            indice_parcial[termino].append(doc_id)

                    doc_id += 1

                    # Volcar a disco cada n documentos
                    if (doc_id % n) == 0:
                        guardar_indice_parcial(
                            indice_parcial, bloque_id, carpeta_salida
                        )
                        indice_parcial = defaultdict(list)
                        print(f"Bloque {str(bloque_id)} terminado")
                        bloque_id += 1

    # Guardar ultimo bloque por si quedo algo
    if len(indice_parcial) > 0:
        guardar_indice_parcial(indice_parcial, bloque_id, carpeta_salida)
        print(f"Bloque {str(bloque_id)} restante terminado")

    # Guardar el mapeo de doc_id a nombre de archivo
    with open(ruta_mapeo, "w", encoding="utf-8") as f:
        json.dump(doc_map, f)


def guardar_indice_parcial(indice, bloque_id, carpeta_salida):
    ruta = os.path.join(carpeta_salida, f"indice_parcial_{bloque_id}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(indice, f)


def merge_indices(directorio_indices, archivo_salida, frecuencias):
    indices = os.listdir(directorio_indices)
    print(f"Mergeando {len(indices)} índices parciales...")

    if frecuencias:
        # acumulador: termino -> {doc_id: freq}, uso dict para sumar frecuencias y luego convertir a lista
        acumulador = defaultdict(dict)

        for nombre_archivo in indices:
            ruta = os.path.join(directorio_indices, nombre_archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                indice_parcial = json.load(f)

                for termino, postings in indice_parcial.items():
                    if termino not in acumulador:
                        acumulador[termino] = {}

                    for doc_freq in postings:
                        doc_id = doc_freq[0]
                        freq = doc_freq[1]
                        if doc_id in acumulador[termino]:
                            acumulador[termino][doc_id] += freq
                        else:
                            acumulador[termino][doc_id] = freq

        # Convertimos a formato lista de pares ordenada
        indice_final = {
            termino: [[doc_id, freq] for doc_id, freq in sorted(postings.items())]
            for termino, postings in acumulador.items()
        }

    else:
        # acumulador: termino -> set(doc_id)
        acumulador = defaultdict(set)
        for nombre_archivo in indices:
            ruta = os.path.join(directorio_indices, nombre_archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                indice_parcial = json.load(f)

                for termino, postings in indice_parcial.items():
                    for doc_id in postings:
                        acumulador[termino].add(doc_id)

        indice_final = {
            termino: sorted(list(doc_ids)) for termino, doc_ids in acumulador.items()
        }

    with open(archivo_salida + ".json", "w", encoding="utf-8") as f:
        json.dump(indice_final, f)

    return indice_final


def buscar_termino(indice, termino, doc_map_file="doc_ids.json"):
    with open(doc_map_file, "r", encoding="utf-8") as f:
        doc_map = json.load(f)
    posting_completa = []
    posting = indice[termino]
    for doc_id, freq in posting:
        nombre = doc_map.get(str(doc_id), "desconocido")
        posting_completa.append(f"{nombre}:{doc_id}:{freq}")

    return posting_completa


nltk.download("punkt")
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

ruta_corpus = "wiki-small"
carpeta_indices = "indices_parciales"
indice_final = "indice"

if len(sys.argv) != 3:
    print("Uso: python buscar_termino.py <n> <termino>")
    sys.exit(1)

n = int(sys.argv[1])
termino = sys.argv[2].lower()

print(f"Procesando con N={n}")

# Para este ejercicio creo un archivo docs_ids.json para mapear el doc_id generado durante la indexacion al nombre de archivo y lo uso para la salida
# En este caso el indice entero se va a componer de ambos archivos: el indice final y el mapeo de las doc_ids

procesar_y_volcar_indice(ruta_corpus, n, carpeta_indices, True)

resultado = merge_indices(carpeta_indices, indice_final, True)

posting_list = buscar_termino(resultado, termino)

print(f"Posting list para '{termino}':")
for entry in posting_list:
    print(entry)
