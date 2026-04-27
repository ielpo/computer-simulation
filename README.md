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

## Simulation Model Specification


**TO REVIEW - written by sloperator**


In order of execution, all other variables are zero-initialized

* ticks-per-year: 100
* coaching-rate-options: Integer list between 0 and max-coaching-rate
* headcount: Rounded normal distribution using global parameters
* hiring-threshold: Rounded normal distribution using global parameters
* coaching-rate: One of integer coaching rates up to global parameter value
* age: Random between 20 and 64, with weighted distribution
* skill-level: Proportional to age with random offset
* turnover-probability: 1

### Timestep

For each tick, developers and companies act in the following sequence:

**Developer actions**

* Decide whether to leave the company (turnover-probability)
* Increase age and check for retirement

**Company actions**

* Fill vacancies (hiring-threshold)
* Choose activity (coaching-rate)
  * _Coaching day_: Developers increase their skill level and the turnover probability decreases (satisfied, growing workers stay).
  * _Working day_: Developers focus on regular work and their turnover probability increases (stagnating workers become more likely to leave). Company revenue increases.
* Update the company strategy at the fixed interval
* Update the color of the patches


- Entities and state:
  - Agents: Developers (turtles) with state variables: `age`, `skill-level`, `turnover-probability`, `last-coaching`.
  - Companies: represented by patches with state: `headcount`, `total-skill`, `hiring-threshold`, `coaching-rate`, `effective-coaching-rate`, `activity`, `revenue`, `cumulative-revenue`, `last-review`.
  - Globals: `ticks-per-year`, `turnovers-this-tick`, `coaching-rate-options`, `market-mean-skill`, `market-mean-revenue` and the set of model parameters controlling hiring, coaching, turnover, decay, and strategy updates.

- Topology: Companies live on patches (one company per patch except patch 0 0 which is the unemployed pool). Developers occupy patches (work for the company on that patch) or patch 0 0 when unemployed.

- Time / Scheduling:
  - Discrete-time, synchronous ticks. One tick is the model's basic time-step; `ticks-per-year` maps ticks to years.
  - Per tick schedule (observer/agent ordering):
    1. Turnover: developers probabilistically leave companies.
    2. Increase age and retire if applicable.
    3. Companies (patches) fill vacancies according to `hiring-threshold`.
    4. Companies choose an `activity` (coach vs work) determined by `coaching-rate` and vacancy pressure.
    5. Companies execute activity: on coaching days developers gain skill and reduce turnover probability; on working days developers gain minimal skill and turnover probability increases; companies accumulate revenue.
    6. Strategy review: at intervals (`strategy-review-interval`) companies may update `hiring-threshold` or `coaching-rate` according to vacancy pressure and configured dynamic strategies.

- Initialization:
  - All state variables zero-initialized, then patches and turtles are initialized.
  - `ticks-per-year` default 100.
  - `coaching-rate-options` is generated as an integer list up to `max-coaching-rate`.
  - Each patch is assigned a `headcount` sampled from a rounded normal distribution (controlled by `headcount-mean` and `headcount-variance`) and a `hiring-threshold` similarly sampled.
  - Developers are created with ages sampled from a distribution biased toward younger ages, `skill-level` initialized proportional to age plus noise, and `turnover-probability` set to 1.

- Key processes (model logic):
  - Turnover: each developer leaves with their personal `turnover-probability` and moves to the unemployed pool (patch 0 0).
  - Hiring: patches attempt to hire until `headcount` is met, selecting candidates whose skill >= `hiring-threshold` (threshold can adjust dynamically).
  - Coaching vs Work: firms split time between coaching (developers gain `coaching-skill-increase`, turnover decreases, less revenue that tick) and working (developers gain `working-skill-increase`, turnover increases, firms earn revenue).
  - Diminishing returns and ceilings: coaching gains can be limited by `coaching-skill-ceiling` and `diminishing-returns-coaching`.
  - Skill decay: optional decay if developers spend long periods without coaching, controlled by `skill-decay-threshold` and `skill-decay-rate`.
  - Strategy updates: at intervals, firms may raise/lower `hiring-threshold` and alter `coaching-rate` based on vacancy pressure, subject to configured ceilings/cutoffs.

- Inputs (parameters): Headcount distribution (`headcount-mean`, `headcount-variance`), hiring thresholds, coaching parameters (`coaching-skill-increase`, `coaching-turnover-decrease`, `max-coaching-rate`, etc.), turnover dynamics (`working-turnover-increase`), skill decay controls, and strategy dynamics (`dynamic-hiring-strategy`, `dynamic-coaching-strategy`, `strategy-review-interval`, `vacancy-rate-cutoff`).

- Outputs / metrics (BehaviorSpace reporters and UI monitors):
  - Market-level: `market-mean-skill`, `market-mean-revenue`, `turnovers-this-tick`.
  - Firm-level (patch reporters): per-patch `revenue`, `cumulative-revenue`, `total-skill`, `hiring-threshold`, `coaching-rate`.
  - Agent-level: `skill-mean`, `turnover-rate` and distributions (skills, age, coaching-rate) used in plots.
  - BehaviorSpace reporters: aggregated metrics such as `revenue-mean`, `skill-mean`, `revenue-at-coaching-rate`, `skill-at-coaching-rate`, `headcount-at-coaching-rate`.


### Pseudocode

```
Function tick:
  For each Agent:
    turnover-probability()
    increase-age()
  For each Company:
    fill-vacancies()
    choose-activity()
  For each Agent in Company:
    If activity is coaching:
      decrease-agent-turnover()
    Else:
      increase-agent-turnover()
      do-work()

Function turnover-probability:
  If random > agent-turnover:
    leave-company()

Function increase-age:
  Increment agent.age
  If agent.age >= 65:
    Die (retire)
    Spawn new Agent

Function fill-vacancies:
  For each vacancy:
    For each unemployed agent:
      If agent.skill >= company.hiring-threshold
        hire-agent()
        Exit loop 

Function do-work:
  Increase company.output
  Increment agent.skill-level
```

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


# Experiments



# Credits
Developed by
- Güntensperger Raphael
- Ielpo Gianluca
- Schütz Michael
- Sutter Svenja
