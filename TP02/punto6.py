from collections import defaultdict
from langdetect import detect


# Metodo 1
def obtener_distribucion_frecuencias(texto):
    frecuencias = {}
    distribucion = {}
    total_letras = 0
    for letra in texto.lower():
        if letra.isalpha():
            # Si no existe inicializo en 0, de lo contrario +1
            frecuencias[letra] = frecuencias.get(letra, 0) + 1
            total_letras += 1
    # Calculo la distribucion de prob.
    for letra, frecuencia in frecuencias.items():
        distribucion[letra] = frecuencia / total_letras
    return distribucion


# Metodo 1
def calcular_distancia(frecuencia_texto, frecuencia_idioma):
    # Unir todas las letras
    letras = set(frecuencia_texto.keys()).union(set(frecuencia_idioma.keys()))
    distancia = 0
    for letra in letras:
        frecuencia_texto_letra = frecuencia_texto.get(letra, 0)
        frecuencia_idioma_letra = frecuencia_idioma.get(letra, 0)
        # Se obtiene el valor absoluto de la resta entre las frecuencias de ambas letras
        # Luego se acumulan para obtener la distancia total
        diferencia = abs(frecuencia_texto_letra - frecuencia_idioma_letra)
        distancia += diferencia
    return distancia


# Metodo 1
def predecir_idioma_distr_frecuencias(texto, frec_english, frec_french, frec_italian):
    frec_linea = obtener_distribucion_frecuencias(texto.strip())
    distancias = {
        "English": calcular_distancia(frec_linea, frec_english),
        "French": calcular_distancia(frec_linea, frec_french),
        "Italian": calcular_distancia(frec_linea, frec_italian),
    }
    # El idioma con menor distancia es el mas cercano
    idioma_predicho = min(distancias, key=distancias.get)
    return idioma_predicho


# Metodo 2
def construir_matriz_probabilidades(texto):
    texto = texto.lower()
    texto = "".join(c for c in texto if c.isalpha())  # Filtrar solo letras
    bigramas = defaultdict(int)
    letras = defaultdict(int)

    # Contar bigramas y letras
    for i in range(len(texto) - 1):
        x = texto[i]
        y = texto[i + 1]
        bigramas[(x, y)] += 1
        letras[x] += 1

    # Calcular las probabilidades
    probabilidades = defaultdict(lambda: defaultdict(float))
    for (x, y), count in bigramas.items():
        # P(y|x) Probabilidad de que siga 'y' dado 'x'
        probabilidades[x][y] = count / letras[x]

    return probabilidades


# Metodo 2
def calcular_distancia_probabilidades(matriz_texto, matriz_idioma):
    distancia = 0
    # Se recorren solo los bigramas que están en ambas matrices
    for x in matriz_texto:
        for y in matriz_texto[x]:
            # Revisamos si el bigrama existe en ambos textos
            prob_texto = matriz_texto.get(x, {}).get(y, 0)
            prob_idioma = matriz_idioma.get(x, {}).get(y, 0)

            # Calculamos la diferencia
            diferencia = abs(prob_texto - prob_idioma)
            distancia += diferencia

    return distancia


# Metodo 2
def predecir_idioma_probabilidades(texto, prob_english, prob_french, prob_italian):
    prob_linea = construir_matriz_probabilidades(texto.strip())
    distancias = {
        "English": calcular_distancia_probabilidades(prob_linea, prob_english),
        "French": calcular_distancia_probabilidades(prob_linea, prob_french),
        "Italian": calcular_distancia_probabilidades(prob_linea, prob_italian),
    }
    # El idioma con menor distancia es el mas cercano
    idioma_predicho = min(distancias, key=distancias.get)
    return idioma_predicho


# Usando langdetect
def predecir_idioma_libreria(texto):
    idiomas = {"en": "English", "fr": "French", "it": "Italian"}
    idioma_predicho = detect(texto.strip())
    return idiomas.get(idioma_predicho, idioma_predicho)


def testear(resultado):
    fallos = {}
    tests = 0
    with open("languageIdentificationData/solution", "r") as f:
        for line in f:
            id, language = line.strip().split()
            if resultado[int(id)] != language:
                fallos[id] = resultado[int(id)] + " | R: " + language
            tests += 1
    if not fallos:
        print("Test Exitoso!")
    else:
        print(f"{str(len(fallos))} de {str(tests)} tests incorrectos")
        print(fallos)


with open("languageIdentificationData/training/English", "r") as f:
    english_text = f.read()
    frec_english = obtener_distribucion_frecuencias(english_text.strip())
    matriz_english = construir_matriz_probabilidades(english_text.strip())

with open("languageIdentificationData/training/French", "r") as f:
    french_text = f.read()
    frec_french = obtener_distribucion_frecuencias(french_text.strip())
    matriz_french = construir_matriz_probabilidades(french_text.strip())

with open("languageIdentificationData/training/Italian", "r") as f:
    italian_text = f.read()
    frec_italian = obtener_distribucion_frecuencias(italian_text.strip())
    matriz_italian = construir_matriz_probabilidades(italian_text.strip())


resultado_distr_frecuencias = {}
resultado_matriz = {}
resultado_libreria = {}

with open("languageIdentificationData/test", "r") as f:
    for i, linea in enumerate(f, 1):
        resultado_distr_frecuencias[i] = predecir_idioma_distr_frecuencias(
            linea, frec_english, frec_french, frec_italian
        )
        resultado_matriz[i] = predecir_idioma_probabilidades(
            linea, matriz_english, matriz_french, matriz_italian
        )
        resultado_libreria[i] = predecir_idioma_libreria(linea)

print("Distribucion de frecuencias: ")
testear(resultado_distr_frecuencias)

print("Matriz de probabilidades:")
testear(resultado_matriz)

print("Usando langdetect: ")
testear(resultado_libreria)
