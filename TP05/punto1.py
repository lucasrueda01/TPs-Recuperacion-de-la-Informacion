import os
import json
import sys
import time
from matplotlib import pyplot as plt
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


def procesar_y_volcar_indice(ruta_corpus, n, carpeta_salida, frecuencias):
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

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


def histograma_posting_lists(indice_final):
    tam_posting_lists = [len(postings) for postings in indice_final.values()]
    plt.figure(figsize=(10, 6))
    plt.hist(tam_posting_lists, bins=50, color="skyblue", edgecolor="black")
    plt.title("Distribución de tamaños de Posting Lists")
    plt.xlabel("Tamaño")
    plt.ylabel("Frecuencia")
    plt.yscale("log")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("distribucion_posting_lists.png")
    plt.show()


def calcular_tamanio_corpus(ruta_corpus):
    tamanio_total = 0
    for root, _, files in os.walk(ruta_corpus):
        for archivo in files:
            ruta_archivo = os.path.join(root, archivo)
            if os.path.isfile(ruta_archivo):
                tamanio_total += os.path.getsize(ruta_archivo)
    return tamanio_total


nltk.download("punkt")
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

ruta_corpus = "wiki-large"
carpeta_indices = "indices_parciales"
indice_final = "indice"

if len(sys.argv) < 2:
    print("Uso: python punto1.py <N> [frecuencias]")
    print("N: Tamaño del bloque de documentos")
    print("frecuencias: (opcional) True para incluir frecuencias, Omitir para no")
    sys.exit(1)

n = int(sys.argv[1])
if len(sys.argv) == 3:
    frecuencias = bool(sys.argv[2])
else:
    frecuencias = False

print(f"Procesando con N={n} y frecuencias={frecuencias}")

inicio = time.time()
procesar_y_volcar_indice(ruta_corpus, n, carpeta_indices, frecuencias)
fin = time.time()
t_indexacion = round(fin - inicio, 4)

inicio = time.time()
resultado = merge_indices(carpeta_indices, indice_final, frecuencias)
fin = time.time()
t_merge = round(fin - inicio, 4)


tamanio_indice = os.path.getsize(indice_final + ".json")
tamanio_docs = calcular_tamanio_corpus(ruta_corpus)
print(tamanio_indice)
print(tamanio_docs)

overhead = (tamanio_indice - tamanio_docs) / (tamanio_docs * 100)

histograma_posting_lists(resultado)

contabilidad = {
    "Tamaño del bloque de documentos (N)": n,
    "Frecuencias": "Si" if frecuencias else "No",
    "Tamaño del índice (mb)": tamanio_indice / (1024 * 1024),
    "Tamaño del corpus (mb)": tamanio_docs / (1024 * 1024),
    "Tiempo de indexacion": t_indexacion,
    "Tiempo de merge": t_merge,
    "Overhead": overhead,
}

print("Contabilidad:")
for clave, valor in contabilidad.items():
    print(f"{clave}: {valor}")
