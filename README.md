# Moneyball your MLB Pitching Staff across Roles

Replication repository for the SSAC27 abstract introducing **FIP_Pyth_WinRate** (a
pitcher's expected win share per nine-inning opportunity) and **FIP_Pyth_WL** (that rate
applied to the opportunities he took).

Shane S. Sanders, Falk College of Sport, Syracuse University.

---

## What is here

```
abstract/   the typeset abstract and the three figures it includes
analysis/   the full analysis as R Markdown, 01 through 05
data/       raw Baseball-Reference exports, Spotrac salaries, derived CSVs
figures/    output directory for figures rendered from the Rmd
scripts/    bare_figs.py, which produced the published matplotlib figures
```

## Rebuilding the abstract

```
cd abstract
pdflatex SSAC27_abstract.tex
pdflatex SSAC27_abstract.tex      # twice, for the figure references
```

Needs `graphicx`, `caption`, `amsmath`, `float`, `geometry`. The three figure files must
sit beside the `.tex`; their names contain spaces and parentheses, which LaTeX handles but
which some build systems do not, so keep them exactly as given.

## Running the analysis

Run the R Markdown files in order; each writes the CSVs the next one reads.

| File | What it does |
|---|---|
| `01_data_and_measures.Rmd` | parses the four season exports, solves the win-neutral anchor `F*`, builds both measures, assigns roles |
| `02_validation.Rmd` | five-input variance decomposition, individual-pitcher persistence, nonparametric test of the Pythagorean exponent |
| `03_ml_and_uncertainty.Rmd` | ridge, random forest and gradient boosting out-of-sample; permutation importance; conformal prediction intervals |
| `04_payroll_arbitrage.Rmd` | individual contracts, closer premium, role by service class, win-flip pricing, reallocation and its simulation |
| `05_figures.Rmd` | R versions of the three abstract figures |

Packages: `tidyverse`, `readxl`, `glmnet`, `ranger`, `gbm`, `plotly`, `patchwork`, `knitr`.

```r
install.packages(c("tidyverse","readxl","glmnet","ranger","gbm","plotly","patchwork","knitr"))
rmarkdown::render("analysis/01_data_and_measures.Rmd")
```

## Data

| File | Contents |
|---|---|
| `pitching_2023.txt`, `Pitching_2024.txt`, `Pitching_2025.txt`, `Pitching_2026_through_sept_1.txt` | Baseball-Reference player pitching exports, one row per pitcher-team stint plus season-total rows for pitchers who changed teams |
| `bbref_2026_teams.csv` | 2026 club pitching and standings, transcribed from the team page and checked against its own totals (2069-2069, league FIP 4.16, 36,691 IP) |
| `pitcher_salaries_2026.xlsx` | the Spotrac salary table as supplied |
| `salaries_2026.csv` | the same, parsed: 819 pitchers with team, role tag and salary |

Two things that bite anyone re-deriving this:

1. **Innings are base-three.** `183.2` is 183 and two-thirds. Parsing it as a decimal
   understates league innings materially. `ip_true()` in `01` handles it.
2. **Multi-team pitchers appear twice.** A `2TM`/`3TM` row is the season total; the rows
   that follow are the per-team stints. Season totals drive the persistence work, stints
   drive role and club aggregation.

## A note on what is and is not established

The persistence and attribution results are on populations, not qualified subsamples. The
club-level version of the persistence test is reported in the paper and *discarded*: at
staff level the ERA-minus-FIP wedge is dominated by team defence, which is persistent, so
the aggregate test measures a fielding corps and reports it as pitching. Only the
individual-pitcher test speaks to the fielding-independent claim.

The payroll gradients are fitted to individual contracts, but the within-role
salary-quality relationship is identified only after conditioning on age, because the
collective bargaining agreement prices service time rather than performance.
