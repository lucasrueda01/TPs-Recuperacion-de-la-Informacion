import os
import re
import shutil
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import numpy as np
import pandas as pd
import pyterrier as pt
from math import log2
import matplotlib.pyplot as plt


def limpiar_query(texto):
    tokens = texto.lower()
    tokens = word_tokenize(tokens)
    filtradas = [t for t in tokens if t.isalnum() and t not in stop_words]
    return " ".join(filtradas)


def leer_docs(archivo):
    documentos = []
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read()
        docs = re.findall(
            r"<DOC>\s*<DOCNO>(\d+)</DOCNO>\s*(.*?)\s*</DOC>", contenido, re.DOTALL
        )
        for doc_id, texto in docs:
            documentos.append({"docno": doc_id, "text": texto})
    return documentos


def leer_queries(archivo):
    queries = []
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read()
        tops = re.findall(
            r"<top>.*?<num>(\d+)</num>.*?<title>\s*(.*?)\s*</title>",
            contenido,
            re.DOTALL,
        )
        for qid, texto in tops:
            texto_limpio = limpiar_query(texto)
            queries.append({"qid": int(qid), "query": texto_limpio})
    return queries


def leer_juicios_relevancia(archivo):
    relevancias = {}
    with open(archivo, "r", encoding="utf-8") as f:
        for linea in f:
            partes = linea.strip().split()
            qid = int(partes[0])
            docid = int(partes[2])
            if qid not in relevancias:
                relevancias[qid] = set()
            relevancias[qid].add(docid)
    return relevancias


def indexar(documentos, path_indice):
    index_path = os.path.abspath(path_indice)
    indexador = pt.IterDictIndexer(index_path)
    index_ref = indexador.index(documentos)
    return index_ref


# ============Calculos==============
def precision_en_10(resultados, relevantes):
    n = 10
    aciertos = 0
    for docno in resultados[:n]:
        if docno in relevantes:
            aciertos += 1
    return aciertos / n


def average_precision(resultados, relevantes):
    q_relevantes = 0
    precisions = []
    for docid, docno in enumerate(resultados, start=1):  # Arranca en 1
        if docno in relevantes:
            q_relevantes += 1
            p = q_relevantes / docid
            precisions.append(p)

    if not precisions:
        return 0

    return sum(precisions) / len(precisions)


def ndcg_10(resultados, relevantes):
    n = 10
    gain = [
        1 if docno in relevantes else 0 for docno in resultados[:n]
    ]  # Vector de gains, 1 si es relevante, 0 si no lo es
    # DCG
    dcg = 0
    for i in range(len(gain)):
        if i == 0:
            dcg += gain[i]
        else:
            dcg += gain[i] / log2(i + 1)
    # IDCG
    ideal_gain = sorted(gain, reverse=True)
    idcg = 0
    for i in range(len(ideal_gain)):
        if i == 0:
            idcg += ideal_gain[i]
        else:
            idcg += ideal_gain[i] / log2(i + 1)
    if idcg != 0:
        ndcg = dcg / idcg
    else:
        ndcg = 0
    return ndcg


def precision_recall_interpolada(resultados, relevantes):
    precisiones = []
    recalls = []

    RR = 0  # Relevantes recuperados
    total_relevantes = len(relevantes)

    for i, docno in enumerate(resultados, start=1):
        if docno in relevantes:
            RR += 1
        precision = RR / i
        recall = RR / total_relevantes

        precisiones.append(precision)
        recalls.append(recall)

    # 11 puntos estandar
    niveles_estandar = np.linspace(0.0, 1.0, 11)
    precisiones_interpoladas = []

    for nivel in niveles_estandar:
        precisiones_en_nivel = [p for p, r in zip(precisiones, recalls) if r >= nivel]
        if precisiones_en_nivel:
            precisiones_interpoladas.append(max(precisiones_en_nivel))
        else:
            precisiones_interpoladas.append(0.0)

    plt.figure(figsize=(8, 5))
    plt.plot(niveles_estandar, precisiones_interpoladas, marker="o", color="blue")
    plt.title("Curva Precision-Recall Interpolada")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.grid(True)
    plt.xticks(niveles_estandar)
    plt.ylim([0, 1])
    plt.savefig("precision_recall_interpolada.png")
    plt.show()


nltk.download("punkt")
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

if not pt.java.started():
    pt.java.init()

path_docs = "vaswani/corpus/doc-text.trec"
path_queries = "vaswani/query-text.trec"
path_indice = "indice-vaswani"
path_relevancias = "vaswani/qrels"

if os.path.exists(path_indice):
    shutil.rmtree(path_indice)

documentos = leer_docs(path_docs)
queries = leer_queries(path_queries)
relevancias = leer_juicios_relevancia(path_relevancias)
indice = indexar(documentos, path_indice)
retr_tfidf = pt.BatchRetrieve(indice, wmodel="TF_IDF")

df_queries = pd.DataFrame(queries)

resultados = retr_tfidf.transform(df_queries)
resultados["docno"] = resultados["docno"].astype(int)
resultados["qid"] = resultados["qid"].astype(int)


p10_scores = []
ap_scores = []
ndcg10_scores = []

metricas_por_query = []
for qid in resultados["qid"].unique():
    # Consigo los documentos recuperados para la query
    resultados_filtrados = resultados[resultados["qid"] == qid]
    docnos = resultados_filtrados["docno"].tolist()

    # Consigo los documentos relevantes para la query
    relevantes = relevancias.get(qid, set())

    p10 = precision_en_10(docnos, relevantes)
    ap = average_precision(docnos, relevantes)
    ndcg10 = ndcg_10(docnos, relevantes)

    p10_scores.append(p10)
    ap_scores.append(ap)
    ndcg10_scores.append(ndcg10)

    metricas_por_query.append({"qid": qid, "P@10": p10, "AP": ap, "NDCG@10": ndcg10})

print("Promedios globales:")
print(f"Precision@10: {np.mean(p10_scores):.4f}")
print(f"Average Precision: {np.mean(ap_scores):.4f}")
print(f"NDCG@10: {np.mean(ndcg10_scores):.4f}")

precision_recall_interpolada(docnos, relevantes)

df_metricas = pd.DataFrame(metricas_por_query)

print("\nMetricas por query: ")
print(df_metricas.to_string(index=False))
