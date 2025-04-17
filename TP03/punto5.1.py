import math
import os
import shutil
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import defaultdict, Counter
from bs4 import BeautifulSoup
import pyterrier as pt


# ----------------Script-------------------------
def preprocesar_documentos(documentos):
    all_tokens = []
    df = defaultdict(int)

    for doc in documentos:
        tokens = doc["text"].lower()
        tokens = word_tokenize(tokens)
        tokens = [
            t for t in tokens if t.isalnum() and t not in stopwords.words("english")
        ]  # Como el texto es en ingles, solo filtro por alfanumerico y saco las stopwords

        all_tokens.append(tokens)

        terminos = set(tokens)
        for term in terminos:
            df[term] += 1

    N = len(documentos)
    return all_tokens, df, N


def calcular_tfidf(all_tokens, df, N):
    doc_pesos = []
    for tokens in all_tokens:  # Lista de listas con los tokens de cada doc
        frecuencias = Counter(tokens)
        pesos = {}
        for termino, frecuencia in frecuencias.items():
            tf = 1 + math.log(frecuencia)
            idf = math.log(N / df[termino])
            pesos[termino] = (
                tf * idf
            )  # Diccionario con el peso tf idf de cada termino del documento
        doc_pesos.append(pesos)
    return doc_pesos


def vector_consulta(query, df, N):
    stop_words = stopwords.words("english")
    tokens = query.lower()
    tokens = word_tokenize(tokens)
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    frecuencias_query = Counter(tokens)
    query_pesos = {}
    for termino, frecuencia in frecuencias_query.items():
        if termino in df:  # Si el termino lo indexe
            tf = 1 + math.log(frecuencia)
            idf = math.log(N / df[termino])
            query_pesos[termino] = tf * idf

    return query_pesos


def buscar(query, doc_pesos, df, N):
    query_pesos = vector_consulta(query, df, N)
    resultados = []
    for i, doc_vector in enumerate(doc_pesos):
        # Similitud del coseno
        numerador = 0
        for t in query_pesos:
            if t in doc_vector:
                numerador += query_pesos[t] * doc_vector[t]

        norm_q = math.sqrt(sum(v**2 for v in query_pesos.values()))
        norm_d = math.sqrt(sum(v**2 for v in doc_vector.values()))
        if norm_q and norm_d:
            denominador = norm_d * norm_q
            sim = numerador / denominador
        else:
            sim = 0
        resultados.append((i, sim))

    resultados.sort(key=lambda x: x[1], reverse=True)  # Ordeno por mayor ranking
    return resultados


# -----------------Pyterrier---------------------
def extraer_texto_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def cargar_wiki_small(ruta):
    documentos = []
    for root, _, files in os.walk(ruta):
        for archivo in files:
            if archivo.endswith(".html"):
                ruta_completa = os.path.join(root, archivo)
                with open(ruta_completa, encoding="utf-8") as f:
                    html = f.read()
                    texto = extraer_texto_html(html)
                    documentos.append({"docno": archivo, "text": texto})
    return documentos


def indexar(documentos, path_indice):
    index_path = os.path.abspath(path_indice)
    indexador = pt.IterDictIndexer(index_path, meta={"docno": 100})
    index_ref = indexador.index(documentos)
    return index_ref


PATH_DOCS = "wiki-small"
documentos = cargar_wiki_small(PATH_DOCS)


# -----------------Pyterrier---------------------
PATH_INDEX = "indice-wiki-small"

if os.path.exists(PATH_INDEX):
    shutil.rmtree(PATH_INDEX)

if not pt.java.started():
    pt.java.init()

index_ref = indexar(documentos, PATH_INDEX)
retr_tfidf = pt.BatchRetrieve(index_ref, wmodel="TF_IDF")

# ----------------Script-------------------------
nltk.download("punkt")
nltk.download("stopwords")

all_tokens, df, N = preprocesar_documentos(documentos)
doc_pesos = calcular_tfidf(all_tokens, df, N)

# ------------------ Comparacion múltiples queries ------------------------
top = 10
queries = [
    "information retrieval",
    "machine learning",
    "climate change",
    "world war",
    "neural networks",
]
for query in queries:
    print(f'Query: "{query}"\n')

    resultados_terrier = retr_tfidf.search(query)
    top_terrier = resultados_terrier.head(top)

    resultados_script = buscar(query, doc_pesos, df, N)

    print(f"Top {top} resultados con Script:")
    for i, score in resultados_script[:top]:
        print(f"Doc: {documentos[i]['docno']} - Score: {score:.4f}")

    print(f"\nTop {top} resultados con PyTerrier:")
    for index, row in top_terrier.iterrows():
        print(f"Doc: {row['docno']} - Score: {row['score']:.4f}")

    print("--------------------------------------------------------")
