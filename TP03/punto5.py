import math
import nltk
from nltk.corpus import abc, stopwords
from nltk.tokenize import word_tokenize
from collections import defaultdict, Counter


def preprocesar_documentos(documentos):
    all_tokens = []
    df = defaultdict(int)

    for doc in documentos:
        tokens = doc.lower()
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
    tokens = query.lower()
    tokens = word_tokenize(tokens)
    tokens = [t for t in tokens if t.isalnum() and t not in stopwords.words("english")]
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


nltk.download("abc")  # Corpus de ejemplo
nltk.download("punkt")
nltk.download("stopwords")
documentos = [
    " ".join(sent) for sent in abc.sents()
]  # Uno las palabras para crear los documentos

all_tokens, df, N = preprocesar_documentos(documentos)
doc_pesos = calcular_tfidf(all_tokens, df, N)

query = "government"
resultados = buscar(query, doc_pesos, df, N)

top = 20
print(f"\nTop {top} resultados:")
for i, score in resultados[:top]:
    print(f"Doc {i} - Score: {score:.4f}")
    print(documentos[i])
    print("------")
