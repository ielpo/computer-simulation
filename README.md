# Using Computer Simulations for Understanding Complex Systems
NetLogo implementation for the course Using Computer Simulations for Understanding Complex Systems.

## Development
Using NetLogo version 7.0.3

## Data Analysis
Python scripts to analyse results of simulation runs and compute statistics.
Could be integrated into NetLogo, as it provides a Python integration.

## Run BehaviorSpace from CLI
Use the helper script to run NetLogo BehaviorSpace experiments in headless mode.

List experiments defined in the model:

```bash
python run_behaviorspace.py --list-experiments
```

Run an experiment:

```bash
python run_behaviorspace.py --experiment coaching-rate-vs-revenue
```

If NetLogo is not on PATH, set `NETLOGO_HOME` or pass `--netlogo-home` / `--headless-cmd`.
Outputs are written to `output/` by default.

## Implementation

### Variables

**Turtle Variables**

| Name                 | Description                    |
|----------------------|--------------------------------|
| age                  | Age in years                   |
| skill-level          | Skill level of agent           |
| turnover-probability | Probability of leaving company |
| last-coaching        | Tick count at last coaching    |

**Patch Variables**

| Name               | Description                                      |
|--------------------|--------------------------------------------------|
| headcount          | Target number of employees                       |
| total-skill        | Sum of skill-level of company                    |
| hiring-threshold   | Minimum skill-level required to hire an agent    |
| coaching-rate      | Amount of time spent training instead of working |
| activity           | Activity chosen for current tick                 |
| revenue            | Revenue of company for current tick              |
| cumulative-revenue | Overall revenue of company                       |
| last-review        | Tick count at last strategy review               |

**Global Variables**

| Name                  | Description                            |
|-----------------------|----------------------------------------|
| ticks-per-year        | Number of ticks in one year            |
| turnovers-this-tick   | Number of agents leaving a company     |
| coaching-rate-options | Coaching rates that companies can use  |
| market-mean-skill     | Mean skill across all employed workers |
| market-mean-revenue   | Mean revenue across all companies      |

**Global Parameters**

| Name                         | Description                                                       |
|------------------------------|-------------------------------------------------------------------|
| headcount-mean               | Mean for headcount distribution                                   |
| headcount-variance           | Variance for headcount distribution                               |
| hiring-threshold-mean        | Mean for hiring threshold distribution                            |
| hiring-threshold-variance    | Variance for hiring threshold distribution                        |
| diminishing-returns-coaching | Enable diminishing returns when coaching                          |
| coaching-skill-ceiling       | Upper limit for skill level with diminished returns               |
| working-turnover-increase    | Increase in turnover probability when working                     |
| coaching-turnover-decrease   | Decrease in turnover probability when coaching                    |
| coaching-skill-increase      | Skill level increase when coaching                                |
| working-skill-increase       | Skill level increase when working                                 |
| skill-decay                  | Enable skill decay when no coaching happens                       |
| skill-decay-threshold        | Threshold after which decay starts                                |
| skill-decay-rate             | Rate at which skill decays per tick                               |
| strategy-review-interval     | Ticks between strategy reviews                                    |
| dynamic-hiring-strategy      | Enable changing hiring threshold when updating strategy           |
| vacancy-rate-cutoff          | Maximal allowed vacancy rate before hiring threshold is decreased |
| hiring-threshold-ceiling     | Upper limit for hiring threshold                                  |
| dynamic-coaching-strategy    | Enable changing the coaching rate when updating strategy          |
| max-coaching-rate            | Maximum allowed coaching rate                                     |
