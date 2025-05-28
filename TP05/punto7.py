import json
import time
import os


# --- Funciones de codificacion y decodificacion ---
def vbyte_encode_number(n):
    bytes_ = []
    while True:
        bytes_.insert(0, n % 128)  # prepend 7 bits
        if n < 128:
            break
        n //= 128
    bytes_[-1] += 128  # set high bit on last byte
    return bytes_


def vbyte_encode_list(nums):
    bytes_ = []
    for n in nums:
        bytes_.extend(vbyte_encode_number(n))
    return bytes(bytearray(bytes_))


def vbyte_decode_stream(bytestream):
    nums = []
    n = 0
    for b in bytestream:
        if b < 128:
            n = 128 * n + b
        else:
            n = 128 * n + (b - 128)
            nums.append(n)
            n = 0
    return nums


def elias_gamma_encode_number(n):
    if n == 0:
        raise ValueError("Elias gamma no codifica 0")
    bin_repr = bin(n)[2:]  # sin el '0b'
    offset = bin_repr[1:]  # bits menos el primero
    unary = "0" * (len(bin_repr) - 1) + "1"
    code = unary + offset
    return code


def bits_to_bytes(bits):
    # Completar con ceros a múltiplo de 8
    if len(bits) % 8 != 0:
        bits += "0" * (8 - len(bits) % 8)
    bytelist = []
    for i in range(0, len(bits), 8):
        byte = bits[i : i + 8]
        bytelist.append(int(byte, 2))
    return bytes(bytelist)


def elias_gamma_encode_list(nums):
    bits = ""
    for n in nums:
        bits += elias_gamma_encode_number(n)
    return bits_to_bytes(bits)


def read_bits_from_bytes(bytestream):
    for b in bytestream:
        for i in reversed(range(8)):
            yield (b >> i) & 1


def elias_gamma_decode_stream(bytestream):
    bits = read_bits_from_bytes(bytestream)
    nums = []
    try:
        while True:
            # leer unary: contar ceros hasta el 1
            zero_count = 0
            while next(bits) == 0:
                zero_count += 1
            # leí el '1', ahora leer offset (zero_count bits)
            offset = 0
            for _ in range(zero_count):
                offset = (offset << 1) | next(bits)
            n = (1 << zero_count) | offset
            nums.append(n)
    except StopIteration:
        return nums


# ---------------------------------------------------


def calcular_dgap(doc_ids):
    if not doc_ids:
        return []
    dgaps = [doc_ids[0]]
    for i in range(1, len(doc_ids)):
        dgaps.append(doc_ids[i] - doc_ids[i - 1])
    return dgaps


def reconstruir_lista_dgap(dgaps):
    lista = []
    for i, val in enumerate(dgaps):
        if i == 0:
            lista.append(val)
        else:
            lista.append(lista[-1] + val)
    return lista


def separar_docid_frecuencia(posting_list):
    docids = [int(doc[0]) for doc in posting_list]
    frecs = [int(doc[1]) for doc in posting_list]
    return docids, frecs


def comprimir_indice(indice, dgap):
    # Abre archivos en modo binario para escritura
    f_postings = open("postings.vb", "wb")
    f_freqs = open("frequencies.gamma", "wb")
    # Diccionario offset {termino: (offset_postings, largo_postings, offset_freq, largo_freq)}
    # Esto es para saber dónde empieza y termina cada posting list y frecuencia
    offset_index = {}
    pos_postings = 0
    pos_freqs = 0

    for termino, posting_list in indice.items():
        docids, frecs = separar_docid_frecuencia(posting_list)
        if dgap:
            docids = calcular_dgap(docids)

        vb_doc_ids = vbyte_encode_list(docids)
        eg_frecs = elias_gamma_encode_list(frecs)

        f_postings.write(vb_doc_ids)
        f_freqs.write(eg_frecs)

        offset_index[termino] = (  # Guardo offsets y tamaños
            pos_postings,
            len(vb_doc_ids),
            pos_freqs,
            len(eg_frecs),
        )

        pos_postings += len(vb_doc_ids)
        pos_freqs += len(eg_frecs)

    f_postings.close()
    f_freqs.close()

    with open("indice_offset.json", "w") as f:
        json.dump(offset_index, f)


def recuperar_posting_comprimido(termino, offset_index, dgap):

    if termino not in offset_index:
        print(f"Término '{termino}' no encontrado")
        return []

    off_post, len_post, off_freq, len_freq = offset_index[termino]

    with open("postings.vb", "rb") as f_post, open("frequencies.gamma", "rb") as f_freq:
        # Muevo el cursor a la posicion del termino
        f_post.seek(off_post)
        posting_bytes = f_post.read(len_post)
        f_freq.seek(off_freq)
        freq_bytes = f_freq.read(len_freq)
    # Decodificar los bytes
    docids = vbyte_decode_stream(posting_bytes)
    frecs = elias_gamma_decode_stream(freq_bytes)

    if dgap:
        docids = reconstruir_lista_dgap(docids)

    # Juntar docids y frecuencias
    posting_list = list(zip(docids, frecs))
    posting_list_compressed = {
        "posting_bytes": posting_bytes,
        "frequency_bytes": freq_bytes,
    }
    return posting_list, posting_list_compressed


def descomprimir_indice(indice, dgap):
    f_postings = open("postings.vb", "rb")
    f_freqs = open("frequencies.gamma", "rb")
    with open("indice_offset.json", "r") as f:
        offset_index = json.load(f)
    indice = {}
    for termino, _ in offset_index.items():
        posting_list, _ = recuperar_posting_comprimido(termino, offset_index, dgap)
        indice[termino] = posting_list

    f_postings.close()
    f_freqs.close()
    return indice


with open("indice.json", "r") as f:
    indice = json.load(f)

inicio = time.time()
comprimir_indice(indice, True)
fin = time.time()
t_compresion = fin - inicio
inicio = time.time()
descomprimir_indice(indice, True)
fin = time.time()
t_descompresion = fin - inicio
print("-------------Con dgap------------------")
print(f"Compresión terminada en {t_compresion:.2f} segundos")
print(f"Descompresión terminada en {t_descompresion:.2f} segundos")
print(f"Tamaño postings.vb: {os.path.getsize('postings.vb')} bytes")
print(f"Tamaño frequencies.gamma: {os.path.getsize('frequencies.gamma')} bytes")


inicio = time.time()
comprimir_indice(indice, False)
fin = time.time()
t_compresion = fin - inicio
inicio = time.time()
descomprimir_indice(indice, False)
fin = time.time()
t_descompresion = fin - inicio
print("-------------Sin dgap------------------")
print(f"Compresión terminada en {t_compresion:.2f} segundos")
print(f"Descompresión terminada en {t_descompresion:.2f} segundos")
print(f"Tamaño postings.vb: {os.path.getsize('postings.vb')} bytes")
print(f"Tamaño frequencies.gamma: {os.path.getsize('frequencies.gamma')} bytes")


# Punto 7.1
with open("indice_offset.json", "r") as f:
    offset_index = json.load(f)

termino = input("Ingrese un termino: ")
print(f"\nRecuperando posting list para término '{termino}':")
posting_descomprimido, posting_comprimido = recuperar_posting_comprimido(
    termino, offset_index, False
)
print("Posting descomprimido:")
print(posting_descomprimido)
print("Posting comprimido:", posting_comprimido["posting_bytes"])
print("Frecuencia comprimida:", posting_comprimido["frequency_bytes"])
