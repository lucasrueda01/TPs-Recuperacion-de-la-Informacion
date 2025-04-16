import math
import nltk
from nltk.corpus import abc, stopwords
from nltk.tokenize import word_tokenize
from collections import defaultdict, Counter


def preprocesar_documentos(documentos):
    stop_words = set(stopwords.words("english"))
    vocabulario = set()
    doc_tokens = []
    df = defaultdict(int)

    for doc in documentos:
        tokens = word_tokenize(doc.lower())
        tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
        doc_tokens.append(tokens)

        unique_terms = set(tokens)
        for term in unique_terms:
            df[term] += 1
        vocabulario.update(tokens)

    N = len(documentos)
    return doc_tokens, df, N


def calcular_tfidf(doc_tokens, df, N):
    doc_vectors = []
    for tokens in doc_tokens:
        tf = Counter(tokens)
        vec = {}
        for term, freq in tf.items():
            tf_weight = 1 + math.log(freq)
            idf = math.log(N / df[term])
            vec[term] = tf_weight * idf
        doc_vectors.append(vec)
    return doc_vectors


def vector_consulta(query, df, N):
    stop_words = set(stopwords.words("english"))
    tokens = word_tokenize(query.lower())
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    tf_query = Counter(tokens)

    query_vec = {}
    for term, freq in tf_query.items():
        if term in df:
            tf_weight = 1 + math.log(freq)
            idf = math.log(N / df[term])
            query_vec[term] = tf_weight * idf

    return query_vec


def buscar(query, doc_vectors, df, N):
    query_vec = vector_consulta(query, df, N)
    resultados = []

    for idx, doc_vec in enumerate(doc_vectors):
        numerador = sum(query_vec[t] * doc_vec.get(t, 0) for t in query_vec)
        norm_q = math.sqrt(sum(v**2 for v in query_vec.values()))
        norm_d = math.sqrt(sum(v**2 for v in doc_vec.values()))
        sim = numerador / (norm_q * norm_d) if norm_q and norm_d else 0
        resultados.append((idx, sim))

    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados


nltk.download("abc")
nltk.download("punkt")
nltk.download("stopwords")
documentos = [
    " ".join(sent) for sent in abc.sents()
]  # Anido las palabras para crear documentos

doc_tokens, df, N = preprocesar_documentos(documentos)
doc_vectors = calcular_tfidf(doc_tokens, df, N)

consulta = "government"
ranking = buscar(consulta, doc_vectors, df, N)

top = 5
print(f"\nTop {top} resultados:")
for idx, score in ranking[:top]:
    print(f"Doc {idx} - Score: {score:.4f}")
    print(documentos[idx])
    print("------")
