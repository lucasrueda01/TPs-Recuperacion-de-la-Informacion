import json


def obtener_skip_list_ordenada_por_docname(indice, docmap, termino):
    if termino not in indice:
        print(f"El término '{termino}' no se encuentra en el índice.")
        return []

    skip_list = indice[termino]["skip_list"]
    resultado = []

    for doc_id_destino, _ in skip_list:
        doc_name = docmap.get(str(doc_id_destino))
        resultado.append((doc_name, doc_id_destino))

    # Ordenar
    resultado.sort(key=lambda x: x[0])

    return resultado


with open("indice_con_skips.json", "r", encoding="utf-8") as f:
    indice = json.load(f)

with open("doc_ids.json", "r", encoding="utf-8") as f:
    docmap = json.load(f)

termino = input("Ingrese el término para ver su skip list: ").strip()

skiplist = obtener_skip_list_ordenada_por_docname(indice, docmap, termino)

print(f"Skip list para '{termino}':")
for doc_name, doc_id in skiplist:
    print(f"{doc_name}:{doc_id}")
