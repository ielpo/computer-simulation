# Using Computer Simulations for Understanding Complex Systems
NetLogo implementation for the course Using Computer Simulations for Understanding Complex Systems.

## Development
- NetLogo version 7.0.3
- uv Python dependency management tool, [docs.astral.sh/uv](https://docs.astral.sh/uv/#installation)

### Data Analysis
Python scripts to analyse results of simulation runs and compute statistics.

### Run BehaviorSpace from CLI
Use the helper script to run NetLogo BehaviorSpace experiments in headless mode.

List experiments defined in the model:

```bash
uv run run_behaviorspace.py --list-experiments
```

Run an experiment:

```bash
uv run run_behaviorspace.py --experiment coaching-rate-vs-revenue
```

If NetLogo is not on PATH, set `NETLOGO_HOME` or pass `--netlogo-home` / `--headless-cmd`.
Outputs are written to `output/` by default.

---

# Modeling

## Conceptual Model

This model explores the effects related to software developer training on company performance within an ecosystem of competing software companies.

Purpose: Explore how company-level training of developers affects firm performance and workforce mobility in an ecosystem of competing software companies.
- **Goal**: Understand how firm-level investment in training affects firm performance, workforce skill distribution, and workforce mobility at both individual and market scale.
- **Research question**: Under which conditions do adaptive hiring and coaching strategies improve long-term firm revenue and retention, and how do they affect market-level skill and turnover dynamics?

Companies invest different amounts in developer training. Developers improve skills and may move between companies, spreading knowledge across the ecosystem.

Companies face a strategic trade-off:
- **Invest in training** to improve developers skills, leading to higher output over time. However, developers are less productive during training and once they become more skilled, they may leave for another company.
- **Hire already skilled developers** and avoid investing in training. This carries the risk that developers may leave due to a lack of growth and if too many companies follow this strategy, it raises the question of how delevopers move on from the junior level.

Model boundaries and scope

- Included: software companies and individual developers, hiring and turnover dynamics, training vs. working trade-offs, simple firm and developer strategy updating.
- Excluded: wages/salaries, project-level allocation, developer specialization, management decisions as well as team dynamics, company-specific knowledge, and software quality.

Model components

- Developer (mobile agent): age, skill level, propensity to leave company.
- Company (immobile agent): target headcount, hiring threshold, training rate, per-tick revenue and cumulative revenue, hiring and training strategy.
- Unemployed pool: place for developers to stay if not assigned to a company, skill stagnates in this state.

| Behavior | Agent | Description |
|---|---|---|
| Determine activity | Company | Each firm has a policy on training, this can be affected by vacancies and is updated at regular intervals. |
| Work | Developer | Execute work for the company, increases the revenue depending on the skill level. Decreases worker satisfaction, slightly increases skill level. |
| Train | Developer | Improve the skills of employees |
| Skill decay | Developer | Represents technological developments, skills get outdated over time. |
| Turnover | Developer | Developers can decide to leave companies and either join the unemployed pool or another company. |
| Hiring | Company | Companies hire from the unemployed pool until target headcount, selecting candidates whose skill meets their criteria. |
| Compare to peers | Company and Developer | Agent can compare itself with its peers. This influences how satisfied a developer is, or how the company updates its strategy. |
| Strategy update | Company | At configured intervals firms may adjust criteria in response to vacancy pressure, performance, and market situation. |

Temporal and spatial scales

- Time: discrete synchronous ticks representing working days, fixed number of ticks in a year.
- Topology: the developer position represents employment relationship, each developer can only be employed by one company at a time.

Initialization and inputs

- Companies and Developers are initialized from parameterized distributions. Coaching-rate options are drawn from a list.
- Key model parameters: coaching gains, turnover adjustments, skill ceilings and decay, strategy review and effect configuration.

Outputs and indicators

- Company: per tick revenue, cumulative revenue, total skill, hiring threshold, coaching rate, turnover rate.
- Developer: skill distribution, age distribution, turnover propensity.
- Market-level: revenue distribution and mean, turnover rate.

Assumptions and limitations

- Hiring is driven by a skill level threshold: no salary or other dynamics are modelled.
- Companies are structurally homogeneous except for stochastic initialization: company heterogeneity beyond these draws is not modelled.
- Behavior of agents: developers differ only by individual state variables. Preferences, network effects, and company reputations are abstracted.

Validation and modeling-cycle mapping

- Conceptual stage: define entities, processes, and hypothesized causal chains (this document).
- Formalization & implementation: the conceptual rules map to NetLogo procedures (`turnover`, `fill-vacancies`, `choose-activity`, `execute-activity`, `do-coaching`, `do-work`, `update-strategy`) in `simulation.nlogox`.
- Verification: unit-check procedures (e.g., hiring fills to headcount when candidates available; coaching reduces turnover) and use small deterministic seeds to reproduce expected micro-level behavior.
- Validation: compare emergent patterns (e.g., revenue vs. coaching-rate curves, market mean skill trajectories) against stylized expectations and sensitivity analyses (toggle `diminishing-returns-coaching`, `skill-decay`, `dynamic-*` strategies).
- Experimentation: use BehaviorSpace sweeps and recording reporters (`revenue-mean`, `skill-mean`, `revenue-at-coaching-rate`, etc.) to test hypotheses and map phase-space of outcomes.

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

## Credits
Developed by
- Güntensperger Raphael
- Ielpo Gianluca
- Schütz Michael
- Sutter Svenja
