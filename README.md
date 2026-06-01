# Memoria TFG — OmniLitter

Repositorio con el código fuente LaTeX de la memoria del Trabajo de Fin de Grado **OmniLitter**, una aplicación móvil de campo para la monitorización de residuos urbanos.

## 📄 Última versión compilada

👉 [Ver memoria (main.pdf)](https://github.com/alecasbar/omnilitter-docs/blob/main/main.pdf)

## Estructura del proyecto

```
├── main.tex                  # Documento principal
├── bibliografia.bib          # Referencias bibliográficas
├── chapters/                 # Capítulos de la memoria
│   ├── 01_introduccion.tex
│   ├── 02_objetivos.tex
│   ├── 03_apps_relacionadas.tex
│   ├── 04_tecnologias_desarrollo.tex
│   ├── 05_requisitos.tex
│   ├── 06_planificacion_gestion.tex
│   ├── 07_diseno_sistema.tex
│   ├── 08_implementacion_desarrollo.tex
│   ├── 09_pruebas_calidad.tex
│   ├── 10_conclusiones_trabajo_futuro.tex
│   └── 11_referencias.tex
├── annexes/                  # Anexos
├── figures/                  # Imágenes y diagramas
└── tables/                   # Tablas
```

## Compilar el proyecto

Requiere una distribución LaTeX (TeX Live, MiKTeX o MacTeX):

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

O abrir `main.tex` directamente con **Overleaf**, **TeXShop** o cualquier editor LaTeX.
