# Explorex — PRD v3.0
## para Agentes de IA y Equipos de Desarrollo

| Campo | Valor |
|---|---|
| Version | 3.0 MVP |
| Fecha | Marzo 2026 |
| Organizacion | DataFluxIT |
| Repositorio | data-x-claude / apps/explorex |
| Estado | En desarrollo activo |

---

## 0. Rol del documento y jerarquia

Este documento es la fuente de verdad para decisiones de producto, UX, alcance y prioridades del MVP de Explorex.

Jerarquia documental:
1. explorex-prd-v3.md -- producto, UX, alcance y prioridades
2. datafluxIT-core-prd.md -- fuente de verdad del core compartido entre todos los productos
3. CLAUDE.md -- contexto operativo para Claude dentro de IntelliJ
4. guidelines.md -- reglas de ejecucion para Junie dentro de IntelliJ
5. core/backend/engine/contracts.py -- fuente de verdad para contratos tecnicos

Si hay conflicto entre este PRD y datafluxIT-core-prd.md sobre lo que es core: prevalece el core PRD.
Si hay conflicto sobre producto, UX o alcance de Explorex: prevalece este PRD.

---

## 1. Vision y Problema

### 1.1 El problema

Las herramientas de analisis con IA suelen mezclar lectura del dataset, inferencia linguistica y calculo estadistico sin dejar claro que parte fue realmente computada. El resultado puede sonar convincente pero no es metodologicamente confiable ni auditable.

Esto genera dos fallas opuestas: el usuario experto desconfia porque no ve trazabilidad, y el usuario no tecnico sobreconfia porque el lenguaje suena seguro.

### 1.2 La solucion

Explorex convierte la exploracion de datos en una experiencia guiada donde el sistema calcula primero e interpreta despues. Tres roles LLM separados (CODER, REVIEWER, INTERPRETER) orquestados via LiteLLM, con un kernel Jupyter ejecutando el codigo real.

| Dimension | Herramientas actuales | Explorex |
|---|---|---|
| Analisis | LLM infiere sobre CSV como texto | CODER genera Python, kernel lo ejecuta |
| Confiabilidad | Plausible pero no verificado | Resultados computados y auditables |
| Graficos | PNG estatico | Plotly interactivo con clicks |
| Exploracion | Chat lineal | Arbol de drill-down interactivo |
| Trazabilidad | No existe | Codigo + audit_summary + node_document por nodo |

### 1.3 Posicionamiento

Explorex no es un chat que opina sobre un CSV. Es una interfaz de exploracion analitica guiada sobre computo real, con auditabilidad y reproducibilidad incorporadas.

---

## 2. Usuarios Objetivo

### 2.1 Usuario primario — No tecnico

| Campo | Valor |
|---|---|
| Rol tipico | Gerente, consultor, dueno de negocio, analista de negocio |
| Conocimiento tecnico | Manejo basico de Excel. No sabe Python. |
| Expectativa de tiempo | Resultado visible en menos de 30 segundos |
| Necesidad de confianza | Quiere saber QUE se calculo, no COMO |

### 2.2 Usuario secundario — Tecnico

| Campo | Valor |
|---|---|
| Rol tipico | Analista de datos, data scientist, consultor tecnico |
| Uso principal | Exploracion rapida antes de analisis profundo |
| Necesidad adicional | Ver codigo bajo demanda, exportar .ipynb |

### 2.3 Lo que el usuario primario NUNCA debe ver

- Codigo Python ni notebooks
- Errores tecnicos — solo mensajes en lenguaje natural
- Tiempos de carga sin feedback visual

---

## 3. El Producto

### 3.1 Descripcion en una linea

Explorex convierte cualquier CSV en un arbol de analisis interactivos: CODER genera Python, REVIEWER lo valida, kernel lo ejecuta, INTERPRETER explica los resultados.

### 3.2 Flujo principal

1. Usuario sube CSV o Excel
2. Sistema lanza automaticamente: "De que habla este dataset?"
3. cache_manager verifica SHA256(dataset_hash + prompt)
   - Cache hit: devuelve nodo cacheado instantaneamente
   - Cache miss: continua
4. CODER LLM genera codigo Python de analisis
5. REVIEWER LLM valida y corrige el codigo
6. Kernel Jupyter ejecuta el codigo sobre el dataset real
7. INTERPRETER LLM genera interpretacion + audit_summary + suggestions + node_document
8. Frontend muestra: grafico Plotly + interpretacion + chips + arbol actualizado
9. Usuario interactua (pregunta / click en grafico / sugerencia) → nuevo ciclo

### 3.3 Tipos de entrada

| Tipo | Como funciona |
|---|---|
| Pregunta libre | Usuario escribe en lenguaje natural |
| Click en grafico | Frontend captura el elemento y lo traduce en prompt para CODER |
| Sugerencia | Usuario toca una de las hasta 3 preguntas del INTERPRETER |

---

## 4. Lo que Explorex toma del Core

El core (data-x-claude/core/) provee sin modificacion:

- ai_runner.py — orquestacion CODER + REVIEWER + INTERPRETER via LiteLLM
- kernel_manager.py — un kernel Jupyter por sesion, DataFrame en memoria
- result_parser.py — matplotlib → Plotly JSON
- cache_manager.py — SHA256(dataset_hash + prompt)
- repository.py — operaciones MongoDB
- prompt_builder.py — acepta templates como parametros
- Contratos Pydantic: ProcessingSession, ProcessingNode, AuditDocument
- Endpoints: /sessions, /analyze, /nodes/{id}/code, /nodes/{id}/document, /export, /health
- Componentes frontend: PlotlyChart, ExplorationTree, AnalysisNode, SuggestionChips, DatasetUpload
- LiteLLM Router con fallback automatico entre modelos
- Cost tracking por rol (coder/reviewer/interpreter)
- Streaming de interpretacion al frontend

Lo que Explorex agrega en apps/explorex/:

- prompts/initial.py — pregunta inicial "De que habla este dataset?"
- prompts/drilldown.py — analisis de elemento clickeado
- prompts/suggestions.py — generacion de sugerencias
- frontend/pages/Explorer.tsx — pagina principal
- frontend/components/result/ — ResultPanel, InterpretationText, AuditSummary

---

## 5. Funcionalidades con Definicion de Terminado

### 5.1 Upload de Dataset
Acepta CSV y Excel. Valida max 100.000 filas. Computa schema y metadata al subir.
TERMINADO: usuario sube CSV real → sesion creada en MongoDB con dataset_hash → kernel inicializado → analisis inicial arranca automaticamente.

### 5.2 Analisis inicial automatico
Sistema lanza "De que habla este dataset?" sin accion del usuario.
TERMINADO: grafico Plotly real + interpretacion en espanol + audit_summary especifico + hasta 3 sugerencias especificas al dataset.

### 5.3 Grafico interactivo con drill-down
Click en elemento genera nuevo nodo hijo. Tipos soportados: bar, line, scatter, pie.
TERMINADO: clickear un elemento genera analisis coherente con ese elemento sin que el usuario escriba nada.

### 5.4 Arbol de exploracion
Sidebar con jerarquia padre-hijo, colapsable, clickeable.
TERMINADO: 3+ niveles de profundidad, clickear nodo previo carga su resultado correctamente.

### 5.5 Auditabilidad por nodo
audit_summary visible para todos. Codigo Python y node_document disponibles para usuario tecnico.
TERMINADO: audit_summary especifico por nodo, usuario tecnico puede ver codigo y documento.

### 5.6 Cache de analisis
Mismo dataset + misma pregunta = resultado instantaneo sin llamar LLMs ni kernel.
TERMINADO: segunda vez que se hace la misma pregunta sobre el mismo dataset responde en menos de 1 segundo.

### 5.7 Exportacion como notebook
Arbol completo → .ipynb ejecutable. Cada nodo = celda markdown + celda codigo.
TERMINADO: .ipynb exportado corre en Jupyter sobre el mismo dataset y reproduce todos los graficos.

---

## 6. Flujos de Error

| Situacion | Mensaje al usuario |
|---|---|
| CODER genera codigo que REVIEWER no puede aprobar | "No pudimos analizar esta pregunta. Podes intentarlo o hacer una pregunta diferente." |
| Kernel falla al ejecutar | Mismo mensaje anterior. Error se loguea internamente. |
| Kernel muere durante sesion | "Tu sesion expiro. Volve a subir el dataset para continuar." Arbol se preserva. |
| Dataset > 100.000 filas | "Este dataset supera el limite de 100.000 filas." |
| CSV malformado | "No pudimos leer este archivo. Asegurate de que sea un CSV valido con encabezados." |
| Timeout 60 segundos | "El analisis tardo demasiado. Intenta con una pregunta mas especifica." |
| Dataset baja calidad (>50% nulos) | Advertencia visible: "Este dataset tiene X% de valores vacios en columna Y." |

---

## 7. Restricciones NO negociables

- El INTERPRETER nunca recibe filas crudas del CSV — solo resultados computados, schema y metadata
- El REVIEWER siempre corre antes de que el kernel ejecute cualquier codigo
- El usuario primario nunca ve Python, notebooks ni errores tecnicos
- El arbol de exploracion nunca se convierte en chat lineal
- El core nunca tiene logica de dominio de Explorex
- Los prompts siempre viven en apps/explorex/backend/prompts/
- Todo analisis persiste generated_code, audit_summary y node_document

---

## 8. Arquitectura — Decisiones Finales MVP

| Tecnologia | Razon |
|---|---|
| LiteLLM | Motor de llamadas LLM. Reemplaza Sphinx CLI. Soporta 100+ modelos, routing, fallback, cost tracking. |
| OpenRouter | Proveedor de acceso a multiples LLMs con una sola API key |
| Jupyter Server local | Un kernel por sesion. DataFrame en memoria entre analisis. |
| matplotlib → Plotly | CODER genera matplotlib (natural para LLMs), backend convierte a Plotly para interactividad |
| MongoDB Atlas | Flexibilidad de schema para arbol de nodos y artefactos por nodo |
| FastAPI + uv | Async nativo, tipado, performance. Siempre uv add, nunca pip install. |
| Zustand | Estado del arbol en frontend |
| Modelos por defecto | CODER: claude-sonnet / REVIEWER: claude-sonnet / INTERPRETER: claude-sonnet |

---

## 9. Metricas de Exito

### Funcionamiento
- Usuario no tecnico obtiene analisis relevante de CSV sin instrucciones
- Drill-down funciona — click genera analisis coherente
- Arbol muestra 3+ niveles correctamente
- Ningun error tecnico visible en happy path
- 3+ sesiones simultaneas sin degradacion

### Valor
- Tiempo a primer insight < 30 segundos
- Sesiones con 2+ nodos > 60%
- Tasa de cache hit en sesiones repetidas

### Operativas (por nodo)
- Latencia coder_ms, reviewer_ms, kernel_ms, interpreter_ms
- Tokens por rol (para optimizar costos)
- Tasa de timeout < 5%
- RAM por sesion activa

---

## 10. Riesgos Criticos

| Riesgo | Mitigacion |
|---|---|
| Costo de tokens: 3 LLMs por nodo | Cache agresivo + cost tracking por rol desde dia 1 |
| Latencia total > 30 segundos | Streaming de interpretacion, reviewer liviano, cache |
| Reviewer bloquea codigo valido | Ajustar prompt para balance seguridad/utilidad |
| Arbol confuso con muchas ramas | Colapsar/expandir nodos, breadcrumbs |
| Kernel por sesion no escala | Monitorear RAM desde dia 1 |

---

## 11. Roadmap de Productos sobre el mismo Core

| Producto | Pregunta inicial | Dominio |
|---|---|---|
| Explorex (este) | De que habla este dataset? | Analisis exploratorio generico |
| Sales Analyzer | Como van las ventas este periodo? | Revenue, pipeline, forecasting |
| Financial Analyzer | Cual es la salud financiera? | P&L, cashflow, margenes |
| HR Analyzer | Como esta la rotacion del equipo? | Headcount, retencion, performance |

Para agregar un producto nuevo: crear apps/{nombre}/ con prompts propios y frontend propio. El core no se toca.

---

## 12. Glosario

| Termino | Definicion |
|---|---|
| CODER | Rol LLM que genera codigo Python a partir del schema y el prompt |
| REVIEWER | Rol LLM que valida y corrige el codigo antes de ejecutarlo |
| INTERPRETER | Rol LLM que interpreta resultados computados. Nunca ve datos crudos. |
| Nodo | Unidad del arbol: trigger + status + grafico + interpretacion + audit_summary + generated_code + node_document |
| Audit summary | Que se calculo, en lenguaje natural. Visible para todos los usuarios. |
| Node document | Documento .md completo del nodo: hallazgos, advertencias, sugerencias. Para usuario tecnico. |
| Drill-down | Click en elemento de grafico que genera nodo hijo con analisis especifico |
| Cache hit | Dataset + pregunta ya analizados — respuesta sin llamar LLMs ni kernel |
| Core | data-x-claude/core/ — motor reutilizable sin logica de dominio |
| App | apps/{nombre}/ — producto especifico con sus prompts y frontend |

---
*Version 3.0 — Marzo 2026 — DataFluxIT*
