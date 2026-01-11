ASSI is defined at district $d$ and month $t$ as:

$$\mathrm{ASSI}_{d,t} = 0.35\,Z(\Delta \mathrm{Enrol}_{d,t}) + 0.35\,Z(\log(1+\mathrm{Updates}_{d,t})) + 0.20\,Z(\mathrm{BioPerEnrol}_{d,t}) + 0.10\,Z(\mathrm{FrictionProxy}_{d,t})$$

Where:
- $\Delta \mathrm{Enrol}_{d,t}$ is month-over-month enrolment growth (smoothed, clipped).
- $\mathrm{Updates}_{d,t} = \mathrm{DemoUpdates}_{d,t} + \mathrm{BioUpdates}_{d,t}$.
- $\mathrm{BioPerEnrol}_{d,t} = (\mathrm{BioUpdates}+1)/(\mathrm{Enrol}+1)$.
- $\mathrm{FrictionProxy}_{d,t} = (\mathrm{DemoUpdates}+1)/(\mathrm{Enrol}+1)$ (proxy for repeat corrections).
- $Z(\cdot)$ is a national z-score for comparability.
