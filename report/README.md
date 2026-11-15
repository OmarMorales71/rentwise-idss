PW3 IDSS REPORT TEMPLATE

Files:
- main.tex: Full LaTeX report template. Set this as the Main document in Overleaf and compile with pdfLaTeX.
- PW3_IDSS_Report.md: Markdown version for editing, drafting, and importing/copying content from Markdown-compatible editors.

IMPORTANT:
Overleaf compiles LaTeX projects; it does not compile a standalone .md file as the main document by default.
To use this project in Overleaf, upload the ZIP via New Project > Upload Project, then compile main.tex.
Keep the Markdown file in the project as a drafting/reference copy, or convert Markdown sections to LaTeX before compiling.

COMPILING LOCALLY (main.tex -> main.pdf)

Requires a TeX distribution (MacTeX / TeX Live). Run the commands from this `report/` folder.

Recommended (latexmk runs pdfLaTeX as many times as needed for the TOC, lists and cross-references):

    cd report
    latexmk -pdf main.tex

Useful variants:

    latexmk -pdf -pvc main.tex   # recompile automatically every time main.tex is saved
    latexmk -c                   # delete auxiliary files (.aux, .log, .toc, ...) and keep main.pdf
    latexmk -C                   # delete auxiliary files AND main.pdf

Without latexmk, run pdfLaTeX twice so the table of contents and references resolve:

    pdflatex main.tex
    pdflatex main.tex

The bibliography is written inline in main.tex (thebibliography), so no bibtex/biber step is needed.

Replace [PLACEHOLDERS] with your project details and adapt all example diagrams, tables, models, and results to your actual work.
