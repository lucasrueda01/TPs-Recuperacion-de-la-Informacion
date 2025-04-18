import os
import shutil
from bs4 import BeautifulSoup
import pyterrier as pt
from scipy.stats import spearmanr


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


def correlacion(r1, r2, n):
    docs1 = r1.head(n)["docno"].tolist()
    docs2 = r2.head(n)["docno"].tolist()
    comunes = list(set(docs1).intersection(docs2))
    if not comunes:
        return None
    ranks1 = [docs1.index(doc) for doc in comunes]
    ranks2 = [docs2.index(doc) for doc in comunes]
    coef, _ = spearmanr(ranks1, ranks2)  # Coeficiente de correlacion
    return coef


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
    "argentina",
]

# -----------Comparacion------------

with open("resultados.txt", "w", encoding="utf-8") as f:
    for query in queries:
        f.write(f"Query: {query}\n")

        r_tfidf = retr_tfidf.search(query)
        r_bm25 = retr_bm25.search(query)

        f.write("TF-IDF:\n")
        f.write(r_tfidf.head(10).to_string(index=False))
        f.write("\n")

        f.write("BM-25:\n")
        f.write(r_bm25.head(10).to_string(index=False))
        f.write("\n")

        for n in [10, 25, 50]:
            coef = correlacion(r_tfidf, r_bm25, n)
            if coef is not None:
                f.write(f"Correlacion (top {n}): {coef:.4f}\n")
            else:
                f.write(f"Sin coincidencias en top {n}\n")

        f.write("---------------------------------------------\n")

print("Resultados guardados en resultados.txt")
