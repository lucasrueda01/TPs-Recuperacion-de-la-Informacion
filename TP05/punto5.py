import json
import math
import time


# Funcion que modifica el indice generado por el punto 1 para que cada termino tenga una skip list
def construir_indice_con_skiplist():
    with open("indice.json", "r", encoding="utf-8") as f:
        indice_original = json.load(f)

    nuevo_indice = {}

    for termino, posting in indice_original.items():
        n = len(posting)
        skip_len = int(math.sqrt(n)) if n > 1 else 0

        # Construir skip list: cada entrada será [doc_id, posicion] cada raiz(n) documentos
        skip_list = []
        if skip_len > 1:
            for i in range(0, n, skip_len):
                doc_id, _ = posting[i]
                skip_list.append([doc_id, i])

        nuevo_indice[termino] = {"posting_list": posting, "skip_list": skip_list}

    with open("indice_con_skips.json", "w", encoding="utf-8") as f:
        json.dump(nuevo_indice, f)


# NO FUNCIONA
def interseccion_con_skips(t1, t2, indice):
    if t1 not in indice or t2 not in indice:
        return []

    postings1 = indice[t1]["posting_list"]
    postings2 = indice[t2]["posting_list"]
    skip_list1 = indice[t1]["skip_list"]
    skip_list2 = indice[t2]["skip_list"]
    resultado = []
    i = 0
    j = 0

    while i < len(postings1) and j < len(postings2):
        doc1 = postings1[i][0]
        doc2 = postings2[j][0]
        if doc1 == doc2:
            resultado.append(doc1)
            i += 1
            j += 1

        # Sin terminar

    return resultado


def probar_queries():
    with open("indice_con_skips.json", "r", encoding="utf-8") as f:
        indice = json.load(f)

    with open("queries_filtradas_q2.txt", "r", encoding="utf-8") as f:
        inicio = time.time()
        for linea in f:
            linea = linea.strip()
            id_query, query = linea.split(":", 1)
            query = query.strip()
            terminos = query.split()
            resultado = interseccion_con_skips(terminos[0], terminos[1], indice)
        fin = time.time()
        tiempo = fin - inicio

    print(f"Tiempo de ejecucion: {tiempo:.4f} segundos")


construir_indice_con_skiplist()

# probar_queries()
