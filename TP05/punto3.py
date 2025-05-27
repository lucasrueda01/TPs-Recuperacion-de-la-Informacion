import json
import boolean

with open("indice.json", "r", encoding="utf-8") as f:
    indice = json.load(f)

with open("doc_ids.json", "r", encoding="utf-8") as f:
    doc_map = json.load(f)


# Obtener posting list
def get_posting(termino):
    termino = termino.lower()
    if termino in indice:
        return set(doc_id for doc_id, _ in indice[termino])
    return set()


# Evaluar expresion booleana recursivamente
# expr es un arbol de expresiones booleanas
def eval_expr(expr):
    if isinstance(expr, boolean.Symbol):  # Caso base
        return get_posting(expr.obj)

    elif isinstance(expr, boolean.NOT):
        all_docs = set(map(int, doc_map.keys()))
        return all_docs - eval_expr(expr.args[0])

    elif isinstance(expr, boolean.AND):
        sets = [eval_expr(arg) for arg in expr.args]
        return set.intersection(*sets)  # Asterisco desempaqueta los sets

    elif isinstance(expr, boolean.OR):
        sets = [eval_expr(arg) for arg in expr.args]
        return set.union(*sets)


# Archivos de salida
output_q2 = open("queries_filtradas_q2.txt", "w", encoding="utf-8")
output_q3 = open("queries_filtradas_q3.txt", "w", encoding="utf-8")

vocabulario = set(indice.keys())

with open("queries.txt", "r", encoding="utf-8") as f:
    for linea in f:
        linea = linea.strip()

        id_query, query = linea.split(':', 1)
        query = query.strip()

        tokens = query.split()

        # Filtrar solo queries con 2 o 3 términos
        if len(tokens) not in [2, 3]:
            continue

        # Verificar si todos los términos están en el vocabulario
        if all(term in vocabulario for term in tokens):
            if len(tokens) == 2:
                output_q2.write(f"{id_query}:{query}\n")
            else:
                output_q3.write(f"{id_query}:{query}\n")

output_q2.close()
output_q3.close()


algebra = boolean.BooleanAlgebra()

