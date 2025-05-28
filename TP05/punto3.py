import json
import re
import time
import boolean

with open("indice.json", "r", encoding="utf-8") as f:
    indice = json.load(f)

with open("doc_ids.json", "r", encoding="utf-8") as f:
    doc_map = json.load(f)

algebra = boolean.BooleanAlgebra()


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


def filtrar_queries(vocabulario):
    output_q2 = open("queries_filtradas_q2.txt", "w", encoding="utf-8")
    output_q3 = open("queries_filtradas_q3.txt", "w", encoding="utf-8")
    with open("EFF-10K-queries.txt", "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            id_query, query = linea.split(":", 1)
            query = query.strip()
            query = re.sub(r"[^a-zñ\s]", "", query)  # Eliminar caracteres especiales
            tokens = query.split()

            # Filtrar solo queries con 2 o 3 terminos
            if len(tokens) not in [2, 3]:
                continue

            # Verificar si todos los terminos estan en el vocabulario
            if all(term in vocabulario for term in tokens):
                if len(tokens) == 2:
                    output_q2.write(f"{id_query}:{query}\n")
                else:
                    output_q3.write(f"{id_query}:{query}\n")

    output_q2.close()
    output_q3.close()


def ejecutar_queries_binarias(op):
    inicio = time.time()
    with open("queries_filtradas_q2.txt", "r", encoding="utf-8") as f:
        for linea in f:
            id_query, query = linea.strip().split(":", 1)
            tokens = query.split()
            t1 = tokens[0]
            t2 = tokens[1]
            if op == "AND":
                expr = algebra.parse(str(t1 + " AND " + t2))
            elif op == "OR":
                expr = algebra.parse(str(t1 + " OR " + t2))
            elif op == "NOT":
                expr = algebra.parse(str(t1 + " AND NOT " + t2))
            resultado = eval_expr(expr)

            # Guardar resultado
            with open(f"resultado_q2_{op}.txt", "a", encoding="utf-8") as out:
                out.write(
                    f"{id_query}:{','.join(map(str, sorted(resultado))) if resultado else 'N/A'}\n"
                )
    fin = time.time()
    tiempo = fin - inicio
    return tiempo


def ejecutar_queries_ternarias(op1, op2):
    inicio = time.time()
    with open("queries_filtradas_q3.txt", "r", encoding="utf-8") as f:
        for linea in f:
            id_query, query = linea.strip().split(":", 1)
            tokens = query.split()
            t1 = tokens[0]
            t2 = tokens[1]
            t3 = tokens[2]
            if op1 == "AND" and op2 == "AND":
                expr = algebra.parse(str(t1 + " AND " + t2 + " AND " + t3))
            elif op1 == "OR" and op2 == "NOT":
                expr = algebra.parse(str("(" + t1 + " OR " + t2 + ") AND NOT " + t3))
            elif op1 == "AND" and op2 == "OR":
                expr = algebra.parse(str("(" + t1 + " AND " + t2 + ") OR " + t3))
            resultado = eval_expr(expr)

            # Guardar resultado
            with open(f"resultado_q3_{op1}_{op2}.txt", "a", encoding="utf-8") as out:
                out.write(
                    f"{id_query}:{','.join(map(str, sorted(resultado))) if resultado else 'N/A'}\n"
                )
    fin = time.time()
    tiempo = fin - inicio
    return tiempo


vocabulario = set(indice.keys())
filtrar_queries(vocabulario)

tiempo_and = ejecutar_queries_binarias("AND")
tiempo_or = ejecutar_queries_binarias("OR")
tiempo_not = ejecutar_queries_binarias("NOT")
print(f"Tiempo AND: {tiempo_and:.2f} segundos")
print(f"Tiempo OR: {tiempo_or:.2f} segundos")
print(f"Tiempo NOT: {tiempo_not:.2f} segundos")
print(
    f"Total tiempo consultas binarias: {tiempo_and + tiempo_or + tiempo_not:.2f} segundos"
)
print("=" * 50)
tiempo_and_and = ejecutar_queries_ternarias("AND", "AND")
tiempo_or_not = ejecutar_queries_ternarias("OR", "NOT")
tiempo_and_or = ejecutar_queries_ternarias("AND", "OR")
print(f"Tiempo AND AND: {tiempo_and_and:.2f} segundos")
print(f"Tiempo OR NOT: {tiempo_or_not:.2f} segundos")
print(f"Tiempo AND OR: {tiempo_and_or:.2f} segundos")
print(
    f"Total tiempo consultas ternarias: {tiempo_and_and + tiempo_or_not + tiempo_and_or:.2f} segundos"
)
