import json
import math
import heapq
from collections import defaultdict, Counter
import re

with open("indice.json", "r", encoding="utf-8") as f:
    indice = json.load(f)

with open("doc_ids.json", "r", encoding="utf-8") as f:
    doc_map = json.load(f)


def tokenizar(text):
    text = re.sub(r"[^a-zñ\s]", "", text.lower().strip())
    tokens = text.split()
    return tokens


def calcular_idf(indice):
    # Calcular IDF de cada termino
    N = len(doc_map)
    idf = {}
    for termino, posting in indice.items():
        df = len(posting)
        idf[termino] = math.log(N / df, 10)
    return idf


# Modelo vectorial con similitud de coseno
def modelo_vectorial(query, indice, idf, k=10):

    query_terms = tokenizar(query)
    query_tf = Counter(query_terms)

    query_vec = {}
    for term, freq in query_tf.items():
        if term in idf:
            query_vec[term] = freq * idf[term]  # TF * IDF
        else:
            continue  # no esta en el indice

    # Calcular la norma del vector de consulta
    query_norm = math.sqrt(sum(w**2 for w in query_vec.values()))

    scores = defaultdict(float)
    doc_norms = defaultdict(float)

    # DAAT: Recorre documento por documento y acumula score
    for termino, q_peso in query_vec.items():
        postings = indice.get(termino, [])
        for doc_id, tf in postings:
            d_peso = tf * idf[termino]  # TF * IDF del documento
            # d_peso = (1 + math.log(tf, 10)) * idf[termino]  # TF-IDF suavizado con log
            scores[doc_id] += q_peso * d_peso  # Acumula score del documento
            doc_norms[doc_id] += d_peso**2  # Acumula para norma del documento

    results = []
    for doc_id, score in scores.items():
        # Norma del query * Norma del documento
        denom = query_norm * math.sqrt(doc_norms[doc_id])
        coseno = score / denom if denom != 0 else 0
        results.append((coseno, doc_id))

    # Obtener los top-k scores mas altos
    top_k = heapq.nlargest(k, results, key=lambda x: x[0])
    return top_k


query = input("Ingrese su consulta: ")

idf = calcular_idf(indice)
top = modelo_vectorial(query, indice, idf)

for score, doc_id in top:
    doc_name = doc_map[str(doc_id)]
    print(f"{doc_name}:{doc_id}:{score:.4f}")
