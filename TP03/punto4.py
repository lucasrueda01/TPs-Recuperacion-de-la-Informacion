import os
import shutil
from bs4 import BeautifulSoup
import pyterrier as pt
from scipy.stats import spearmanr

# ----------- Preprocesamiento ------------


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


# ----------- Indexación ------------


def indexar(documentos, path_indice):
    index_path = os.path.abspath(path_indice)
    indexador = pt.IterDictIndexer(index_path, meta={"docno": 100})
    index_ref = indexador.index(documentos)
    return index_ref


# ----------- Comparación de rankings ------------


def correlacion(r1, r2, n):
    docs1 = r1.head(n)["docno"].tolist()
    docs2 = r2.head(n)["docno"].tolist()
    comunes = list(set(docs1).intersection(docs2))
    if not comunes:
        return None
    ranks1 = [docs1.index(doc) for doc in comunes]
    ranks2 = [docs2.index(doc) for doc in comunes]
    coef, _ = spearmanr(ranks1, ranks2)
    return coef


# ----------- Configuración inicial ------------

PATH_DOCS = "wiki-small"
PATH_INDEX = "indice-wiki-small"

if os.path.exists(PATH_INDEX):
    shutil.rmtree(PATH_INDEX)

if not pt.java.started():
    pt.java.init()

documentos = cargar_wiki_small(PATH_DOCS)
index_ref = indexar(documentos, PATH_INDEX)

retr_tfidf = pt.BatchRetrieve(index_ref, wmodel="TF_IDF")
retr_bm25 = pt.BatchRetrieve(index_ref, wmodel="BM25")

queries = [
    "information retrieval",
    "machine learning",
    "climate change",
    "world war",
    "neural networks",
]

# ----------- Evaluación y salida ------------

for query in queries:
    print(f"\n🔍 Query: {query}")
    r_tfidf = retr_tfidf.search(query)
    r_bm25 = retr_bm25.search(query)

    for k in [10, 25, 50]:
        coef = correlacion(r_tfidf, r_bm25, k)
        print(
            f"  📏 Correlación (top {k}): {coef:.4f}"
            if coef is not None
            else f"  ⚠️ Sin coincidencias en top {k}"
        )
