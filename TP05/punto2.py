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


algebra = boolean.BooleanAlgebra()

consulta = input(
    "Ingrese la consulta booleana (ej: (apple AND NOT banana) OR orange): "
)

expr = algebra.parse(consulta)
resultado = eval_expr(expr)

print(f"\nResultados ({str(len(resultado))}):")
for doc_id in sorted(resultado):
    nombre = doc_map.get(str(doc_id), "desconocido")
    print(f"{nombre}:{doc_id}")
