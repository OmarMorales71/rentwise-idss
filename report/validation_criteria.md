# Criterios de validación: d_max, bandas de precio y parámetros del conocimiento

Este documento explica y defiende cómo se fijan tres grupos de parámetros del IDSS. Es la base del capítulo 6. Los números salen de:

- `scripts/calibrate_parameters.py` → `results/calibration.md` (elección en validación)
- `scripts/evaluate_test.py` → `results/test_evaluation.md` (evaluación final, una sola vez)

## 0. Regla general: dónde se elige y dónde se evalúa

| Conjunto | Periodo | Listings | Uso |
|---|---|---|---|
| Ajuste | antes de sept. 2019 | 43,765 | Entrenar los modelos con los que se calibra |
| Validación | sept.–nov. 2019 | 36,546 | **Todas las elecciones** (α, k, d_max, b₁, b₂, parámetros del conocimiento) |
| Train | antes de dic. 2019 | 80,311 | Modelo final evaluado en test |
| Test | dic. 2019 | 7,141 | Evaluación final, **una sola vez, sin elegir nada** |

**Por qué:** si un parámetro se elige mirando el test y después se informan resultados sobre ese mismo test, los resultados son optimistas (fuga de información). Separar validación y test es la práctica estándar y la exige el propio informe (cap. 5: "the test set is not used for any choice").

**Por qué 43k/36k y no 80/20:** los datos llegan en cuatro tandas (dic. 2018, feb. 2019, sept. 2019, dic. 2019). Un corte temporal solo puede caer entre tandas. Partir la tanda de septiembre por la mitad sería en la práctica un reparto aleatorio (listings de los mismos días a ambos lados) y perdería el sentido temporal. La validación solo ordena candidatos; el modelo final se reentrena con el train completo.

---

## 1. d_max: distancia media máxima de los comparables

### Qué es
El cap. 2 dice que no se emite juicio de precio si los comparables son "too small or too dissimilar". El cap. 5 lo concreta: la evidencia es suficiente si KNN encuentra k = 10 comparables **y** su distancia media estandarizada (superficie, dormitorios, baños) es ≤ d_max.

### Criterio
**d_max = percentil 95 de la distancia media d̄ en validación**, redondeado hacia arriba a dos decimales. Resultado: **d_max = 1.69**.

### Por qué este criterio
1. **Lo que se buscaba primero no funciona con estos datos.** La opción natural era fijar d_max donde el error de la referencia "se dispara". En validación, el MAPE de Ridge por decil de d̄ va de 16.6% a 23.0%, sin un salto claro y sin crecer de forma monótona (decil 7: 23.0%; decil 10: 20.3%). No hay punto de corte que defender con el error.
2. **Un percentil expresa la idea de "demasiado distinto" directamente.** Un listing es atípico si sus comparables están más lejos que en el 95% de los casos. Es una definición relativa a lo que el sistema ve habitualmente, no un número inventado.
3. **Protege la oportunidad (U2) sin castigar el esfuerzo (U3).** Solo el 5% de los listings de validación queda sin juicio de precio por este motivo, así que no manda a Review una gran parte de los casos (cap. 1, *search effort*).
4. **Por qué 95 y no 90 o 99.** El 95 es el umbral convencional para "fuera de lo habitual". Con el 90 se duplicaría la proporción sin juicio sin una mejora de error que lo justifique; con el 99 el criterio sería casi decorativo.

### Alternativas descartadas
- **Sin criterio de distancia (solo n ≥ 10):** deja vacío el "too dissimilar" del cap. 2.
- **Umbral por error:** no hay relación clara entre d̄ y el error (punto 1).

### Lo que hay que reconocer (limitación para el cap. 6)
- La separación de error es débil. En test, los listings con evidencia suficiente tienen un MAPE del 17.8% y los marcados como insuficientes, del 18.7%. El criterio identifica listings **atípicos para su zona** (en test: mediana de 1,459 sq ft y 3 dormitorios, frente a 766 sq ft y 1 dormitorio del test en general), no listings con una referencia mucho peor.
- La proporción marcada depende del periodo: un 4.9% en validación y un 12.9% en test, porque el test tiene más unidades grandes en ciudades donde el entrenamiento casi no tiene pisos así. No se reajusta, porque el test no se usa para elegir.
- Defensa: d_max es una salvaguarda de **explicabilidad**. Si los comparables que se muestran no se parecen al piso, el sistema no basa un juicio en ellos.

---

## 2. Bandas de precio b₁ y b₂

### Qué son
El gap es g = (precio pedido − referencia) / referencia. Las bandas ubican el precio pedido:
below (g < −b₁) · in line (|g| ≤ b₁) · moderately above (b₁ < g ≤ b₂) · significantly above (g > b₂).

### Criterio
Sobre los listings de validación con evidencia suficiente:
- **b₁ = percentil 50 del |gap| = 0.16**
- **b₂ = percentil 90 del |gap| = 0.49**

### Por qué este criterio
1. **Lo pide el informe.** El cap. 2 dice que las bandas se derivan "from the deviations observed between asking rents and their reference values during validation". Los percentiles del gap son exactamente esas desviaciones.
2. **b₁ = P50: "in line" significa "una desviación normal".** La mitad de los listings reales se desvía de su referencia en menos de un 16%. Llamar "caro" a algo que se desvía menos que el listing típico no estaría justificado, porque esa diferencia la explica lo que el modelo no ve (estado del piso, barrio, etc.).
3. **b₂ = P90: "significantly above" significa "más caro que el 90% del mercado respecto a su referencia".** Esta posición puede producir un Skip (regla R2), y un Skip injustificado daña U2. Por eso el umbral es exigente: un Skip por precio solo ocurre con desviaciones que pocas veces se ven.
4. **Las bandas iniciales (±10% / +25%) eran demasiado estrechas.** Con ellas, el 23.9% de los listings de validación salía "significantly above" y solo el 33% "in line". Con las calibradas: 49.0% in line y 9.7% significantly above. En test (sin reajustar) da 54.9% y 6.7%, cerca de lo esperado.

### Alternativas descartadas
- **Umbrales "de sentido común" (10% / 25%):** no reflejan la dispersión real de los alquileres pedidos; la mitad de los listings normales queda fuera de "in line".
- **Bandas por ciudad:** muchas ciudades tienen muy pocos listings (cap. 4) y los percentiles serían inestables.

### Lo que hay que reconocer
- Las bandas son anchas porque la referencia tiene un error del orden del 14–16% (MdAPE). Si el modelo mejora, las bandas deben recalibrarse.
- La referencia subestima los alquileres más recientes: mediana del gap de +4.2% en validación y +3.7% en test (deriva temporal). Las bandas absorben parte de esa deriva.
- Las bandas se calibran con el modelo entrenado solo con el conjunto de ajuste (43k), que tiene algo más de error que el modelo final. Eso las hace un poco más anchas, es decir, más prudentes, lo cual va a favor de U2.

---

## 3. Parámetros del conocimiento

### Cuáles
Tolerancias de las funciones de satisfacción (`BUDGET_TOLERANCE` 0.20, `SQUARE_FEET_TOLERANCE` 0.25, `BEDROOMS_BAND` 2.0, `BATHROOMS_BAND` 1.0) y umbrales del personal fit (`FIT_VERY_LOW` 0.40, `FIT_GOOD` 0.70). El cap. 3 dice que son valores iniciales del equipo "tuned during validation".

### El problema
**No hay etiquetas.** Nadie sabe cuál "debería" ser la recomendación correcta para un listing y un inquilino, así que no se pueden optimizar como un modelo supervisado. Por eso se valida el comportamiento del sistema, no su acierto.

### Criterio
**Análisis de sensibilidad, un parámetro cada vez**, sobre 10,000 listings de validación, cada uno con un inquilino simulado. Cada parámetro recorre una rejilla de 5 valores alrededor del inicial (±25% para las tolerancias; ±0.05 y ±0.10 para los umbrales). Un valor se acepta si cumple dos condiciones:

- **C1 (esfuerzo de búsqueda, U3): Review ≤ 50% de las evaluaciones.** Si el sistema devuelve más de la mitad de los casos al inquilino, no le ahorra trabajo (cap. 1: "a useful system must also set aside the listings that clearly do not deserve that effort, instead of sending every case back to the renter").
- **C2 (estabilidad): mover el parámetro al valor vecino de la rejilla cambia la clase de ≤ 10% de las evaluaciones.** Un valor inicial elegido por el equipo es defendible si la recomendación no depende de forma crítica del número exacto.

**Regla de decisión:** si el valor inicial cumple C1 y C2, se mantiene. Si no, se elige el valor de la rejilla más cercano que las cumpla. Si ninguno las cumple, se mantiene el inicial y se informa como limitación.

### Resultado
Los seis valores iniciales cumplen C1 y C2, así que **se mantienen**.
- Review: 47.7% en validación y 41.8% en test (≤ 50%).
- Cambio de clase en el valor vecino: entre 0.4% y 4.5% para todos los parámetros; el más sensible es `FIT_GOOD`, con un 4.3–4.5%.

### Por qué un inquilino simulado y cómo es
Hace falta un inquilino para evaluar el personal fit, y no hay datos de inquilinos reales. La población simulada (`scripts/_renters.py`, semilla fija) es explícita y reproducible:

- busca en la ciudad del listing;
- presupuesto = alquiler típico local para los dormitorios que quiere × U(0.85, 1.25);
- dormitorios = los del listing −1, igual o +1 (25% / 50% / 25%);
- superficie = mediana local para esos dormitorios × U(0.85, 1.15);
- baños = 1, 1.5 o 2;
- pesos U(0.2, 0.9); presupuesto no negociable con probabilidad 0.25 y dormitorios con 0.15;
- cada una de cinco amenities habituales con probabilidad 0.3; perros no negociable con probabilidad 0.2 y gatos con 0.1.

"Local" significa los datos que el sistema conoce (ajuste en validación, train en test), por ciudad y dormitorios, con el estado y luego todo el dataset como respaldo.

**Defensa:** la población no pretende representar a los inquilinos reales. Es un banco de pruebas amplio que activa todos los criterios y todas las reglas (R1–R4 aparecen todas) y que permite comparar valores de parámetros en igualdad de condiciones.

### Lo que hay que reconocer
- El análisis valida estabilidad y comportamiento, **no** que las recomendaciones sean correctas. Eso solo podría hacerse con inquilinos reales (trabajo futuro).
- Los umbrales C1 (50%) y C2 (10%) son decisiones del equipo, derivadas de los objetivos del cap. 1, no valores de la literatura.
- C1 depende también de factores ajenos a estos parámetros: falta de evidencia de precio (9.5% de Reviews en test) y datos que el anuncio no indica (55% sin política de mascotas, cap. 4).
- Un parámetro cada vez no captura interacciones entre parámetros.

---

## Preguntas probables y respuesta corta

| Pregunta | Respuesta |
|---|---|
| ¿Por qué no elegisteis los parámetros con el test? | Porque los resultados del test serían optimistas. Todo se elige en validación y el test se usa una vez. |
| ¿Por qué el percentil 95 para d_max? | Porque el error no tiene un punto de ruptura; el P95 define "atípico" como lo que el sistema ve en menos del 5% de los casos. |
| ¿Por qué las bandas son tan anchas (16% / 49%)? | Porque son las desviaciones que muestran los listings reales frente a su referencia. Unas bandas más estrechas llamarían "caro" al listing típico. |
| ¿Cómo validáis el conocimiento sin etiquetas? | Con un análisis de sensibilidad sobre inquilinos simulados: el sistema no manda a Review más de la mitad de los casos y la recomendación no depende del valor exacto de ningún parámetro. |
| ¿d_max sirve para algo si el error apenas cambia? | Garantiza que los comparables que se muestran se parecen al piso. Es una salvaguarda de explicabilidad, y su efecto sobre el error es pequeño. |
