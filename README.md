# Using Computer Simulations for Understanding Complex Systems
NetLogo implementation for the course Using Computer Simulations for Understanding Complex Systems.

## Development
- NetLogo version 7.0.3
- uv Python dependency management tool, [docs.astral.sh/uv](https://docs.astral.sh/uv/#installation)

## Setup

Run `uv sync` to install all dependencies.

### Data Analysis
Python scripts to analyse results of simulation runs and compute statistics.

### Run BehaviorSpace from CLI
Use the helper script to run NetLogo BehaviorSpace experiments in headless mode.

First, adapt the `NETLOGO_CONSOLE` and `THREAD_COUNT` variables to your setup.
Then you can run experiments with
```bash
uv run run_experiments.py
```

The program lists the experiments and allows to select which ones to run.

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
| Determine activity | Company | Each firm has a policy on training, this can be affected by other factors and is updated at regular intervals. |
| Work | Developer | Execute work for the company, increases the revenue depending on the skill level. Decreases worker satisfaction, slightly increases skill level. |
| Train | Developer | Improves the skill level and worker satifsaction. |
| Skill decay | Developer | Represents technological developments, skills get outdated over time. |
| Turnover | Developer | Developers can decide to leave their company and either join the unemployed pool or another company. The company keeps track of the skill level and age of employees that left, this influences the propensity to leave of the remaining developers. |
| Hiring | Company | Companies hire from the unemployed pool until target headcount, selecting candidates whose skill meets their criteria. |
| Strategy update | Company | At configured intervals firms may adjust criteria in response to vacancy pressure, performance, and market situation. |

Temporal and spatial scales

- Time: discrete synchronous ticks representing working days, fixed number of ticks in a year.
- Topology: the developer position represents employment relationship, each developer can only be employed by one company at a time.

Initialization and inputs

- Companies and Developers are initialized from parameterized distributions. Coaching-rate options are drawn from a list.
- Key model parameters: coaching gains, turnover adjustments, skill ceilings and decay, strategy review and effect configuration.

Outputs and indicators

- Company: cumulative revenue, coaching rate, vacancies, mean worker propensity to leave (worker dissatisfaction).
- Market-level: skill distribution mean and standard deviation, unemployment rate.

Assumptions and limitations

- Hiring is driven by a skill level threshold: no salary or other dynamics are modelled.
- Companies are structurally homogeneous except for stochastic initialization: company heterogeneity beyond these draws is not modelled.
- Behavior of agents: developers differ only by individual state variables. Preferences, network effects, and peer effects are abstracted.

## Simulation Model Specification

### Elements and Structure

**Entities and State**

- Agents: Developers (turtles) with state variables: `age`, `skill-level`, `propensity-to-leave`, `last-coaching`.
- Companies: represented by patches with state: `headcount`, `total-skill`, `hiring-threshold`, `coaching-rate`, `effective-coaching-rate`, `activity`, `revenue`, `cumulative-revenue`, `last-review`, `developer-history`, `developers-leaving`.
- Globals: `ticks-per-year`, `turnovers-this-tick`, `coaching-rate-options`, `developer-history-count`, `market-mean-skill`, `market-mean-revenue` and the set of GUI model parameters controlling hiring, coaching, turnover, decay, and strategy updates.

**Topology**

Companies live on patches (one company per patch except `patch 0 0` which is the unemployed pool). Developers occupy patches (work for the company on that patch) or `patch 0 0` when unemployed.

**Time and Scheduling**

- Discrete-time, synchronous ticks. One tick is the model's basic time-step; `ticks-per-year` maps ticks to years.
- Per tick schedule (observer/agent ordering):
  1. Developers decide whether to leave the company, `propensity-to-leave` over threshold
  2. Developers increase age and check for retirement
  3. Companies fill vacancies based on `hiring-threshold`
  4. Companies choose activity, with probability `coaching-rate`
    - _Coaching day_: developers increase their skill level and their `propensity-to-leave` decreases (satisfied, growing workers stay).
    - _Working day_: developers focus on regular work and their `propensity-to-leave` increases (stagnating workers become more likely to leave). Company revenue increases.
  5. Update the company strategy at the fixed interval

**Initialization**

- All state variables zero-initialized, then patches and turtles are initialized.
- `ticks-per-year` default 100.
- `coaching-rate-options` is generated as an integer list up to `max-coaching-rate`.
- Each patch is assigned a `headcount` sampled from a rounded normal distribution (controlled by `headcount-mean` and `headcount-variance`) and a `hiring-threshold` similarly sampled.
- Developers are created with ages sampled from a distribution biased toward younger ages, `skill-level` initialized proportional to age plus noise, and `turnover-probability` set to 1.

**Model logic**

- Turnover: each developer leaves with their personal `turnover-probability` and moves to the unemployed pool (patch 0 0).
- Hiring: patches attempt to hire until `headcount` is met, selecting candidates whose skill >= `hiring-threshold` (threshold can adjust dynamically).
- Coaching vs Work: firms split time between coaching (developers gain `coaching-skill-increase`, turnover decreases, less revenue that tick) and working (developers gain `working-skill-increase`, turnover increases, firms earn revenue).
- Diminishing returns and ceilings: coaching gains can be limited by `coaching-skill-ceiling` and `diminishing-returns-coaching`.
- Skill decay: optional decay if developers spend long periods without coaching, controlled by `skill-decay-threshold` and `skill-decay-rate`.
- Strategy updates: at intervals, firms may raise/lower `hiring-threshold` and alter `coaching-rate` based on vacancy pressure, subject to configured ceilings/cutoffs.

**Parameters**

 Headcount distribution (`headcount-mean`, `headcount-variance`), hiring thresholds, coaching parameters (`coaching-skill-increase`, `coaching-turnover-decrease`, `max-coaching-rate`, etc.), turnover dynamics (`working-turnover-increase`), skill decay controls, and strategy dynamics (`dynamic-hiring-strategy`, `dynamic-coaching-strategy`, `strategy-review-interval`, `vacancy-rate-cutoff`).

**Outputs**
- Market-level: `market-mean-skill`, `market-mean-revenue`, `turnovers-this-tick`.
- Firm-level (patch reporters): per-patch `revenue`, `cumulative-revenue`, `total-skill`, `hiring-threshold`, `coaching-rate`.
- Agent-level: `skill-mean`, `turnover-rate` and distributions (skills, age, coaching-rate) used in plots.
- BehaviorSpace reporters: aggregated metrics such as `revenue-mean`, `skill-mean`, `revenue-at-coaching-rate`, `skill-at-coaching-rate`, `headcount-at-coaching-rate`.

### Pseudocode

```
===============================
INITIALIZATION
===============================

Function setup:
  Initialize variables
  setup-patches()
  setup-turtles()

Function setup-patches:
  For each patch except patch(0,0):
    Initialize headcount and hiring-threshold from normal distributions
    Set coaching-rate from options
    Create 'headcount' developers on patch

Function setup-turtles:
  For each developer:
    age = weighted random from 20-65 years
    skill-level = initial-skill(age)
    propensity-to-leave = 0
    last-coaching = 0
  Update all patch total-skill

Function initial-skill(age) -> number:
  Return 1000 + ((age - 20) / 45) * 6000 + random offset

Function age-probability(age) -> float:
  If age < 30: return (age - 20) / 10
  Else: return 1

===============================
MAIN SIMULATION LOOP
===============================

Function go:
  turnovers-this-tick = 0
  For each developer:
    turnover()
    increase-age()

  update-market-stats()
  
  For each company:
    revenue = 0
    Trim developer-history to max size
    fill-vacancies()
    choose-activity()
    execute-activity()

    Update total-skill = sum of developers' skills
    If activity is "work": revenue = total-skill
    Add revenue to cumulative-revenue
    
    If dynamic-hiring-strategy and time for review:
      update-strategy()
  
===============================
DEVELOPER BEHAVIORS
===============================

Function turnover:
  For each developer in company:
    If propensity-to-leave > leaving-threshold:
      Move developer to unemployed pool (patch 0,0)
      Record developer state in company's developer-history
      Increment turnovers-this-tick

Function increase-age:
  For each developer:
    Increment age by (1 / ticks-per-year)
    If age >= 65:
      Remove developer (retire)
      Spawn new developer with age 20-30
      Set skill-level = initial-skill(20)

Function do-coaching:
  If diminishing-returns-coaching:
    skill-level += coaching-skill-increase * (1 - skill-level / coaching-skill-ceiling)
  Else:
    skill-level += coaching-skill-increase
  propensity-to-leave -= coaching-turnover-decrease (min 0)
  last-coaching = current tick

Function do-work:
  skill-level = min(skill-level + working-skill-increase, coaching-skill-ceiling)
  appeal = company-appeal(skill-level, company's developer-history)
  propensity-to-leave -= appeal * 0.1
  propensity-to-leave += working-turnover-increase
  
  If skill-decay enabled and (ticks since last-coaching) > skill-decay-threshold:
    skill-level *= (1 - skill-decay-rate / ticks-per-year)

===============================
COMPANY LOGIC
===============================

Function fill-vacancies:
  vacancies = headcount - developers on patch
  If vacancies > 0:
    candidates = unemployed developers with skill >= hiring-threshold
    If any candidates:
      Hire random candidates up to vacancy count

Function choose-activity:
  If no developers on patch: return
  
  effective-coaching-rate = coaching-rate
  If vacancy-rate-pressure:
    vacancy-rate = 1 - (developer-count / headcount)
    effective-coaching-rate *= (1 - vacancy-rate)
  
  If random < effective-coaching-rate:
    activity = "coach"
  Else:
    activity = "work"

Function execute-activity:
  If no developers on patch: return
  
  If activity = "coach":
    For each developer: do-coaching()
  Else if activity = "work":
    For each developer: do-work()

Function company-appeal(skill-level, developer-history) -> number:
  appeal = 0
  For each departure in developer-history:
    ratio = ln(skill-level / departure.skill) ^ 2
    weight = 1 / (current-tick - departure.tick + 1)
    appeal += ratio * weight
  Return appeal

Function update-strategy:
  vacancy-rate = 1 - (developer-count / headcount)
  
  If vacancy-rate > vacancy-rate-cutoff:
    hiring-threshold *= 0.7  (lower threshold to hire more)
  Else:
    hiring-threshold *= 1.1  (raise threshold to be selective)
  
  Clamp hiring-threshold: [100, hiring-threshold-ceiling]

Function color-patches:
  For each company patch:
    vacancy-rate = 1 - (developer-count / headcount)
    Patch color scales from grey (0 vacancies) to black (all vacancies)

===============================
MARKET STATISTICS
===============================

Function update-market-stats:
  market-mean-skill = mean skill-level of all employed developers
  market-mean-revenue = mean cumulative-revenue of all companies

===============================
REPORTERS (Data Collection)
===============================

Function revenue-distribution -> [mean, std-dev, median] of revenue across companies

Function skill-distribution -> [mean, std-dev, median] of skill-level across employed developers

Function turnover-rate -> number: turnovers-this-tick

Function unemployment-rate -> number: (unemployed developers) / (all developers)

Function headcount-of-companies -> list of headcount values for each company

Function dependent-variables -> [revenue, coaching, vacancies, propensity]:
  For each company return:
    - cumulative-revenue
    - coaching-rate
    - vacancy count
    - mean propensity-to-leave of developers
```

## Implementation

### Variables

**Developer Variables**

| Name | Description | Initialization |
|---|---|---|
| `age` | Age in years | Weighted distribution 20-65 |
| `skill-level` | Skill level of agent | Proportional to age with random offset |
| `propensity-to-leave` | Dissatisfaction with current company, if greater than `leaving-threshold` turnover | 0 |
| `last-coaching` | Tick count at last coaching | 0 |

**Company Variables**

| Name               | Description                                      | Initialization |
|--------------------|--------------------------------------------------|---|
| `headcount`          | Target number of employees                       |  |
| `total-skill`        | Sum of skill-level of company                    |  |
| `hiring-threshold`   | Minimum skill-level required to hire an agent    |  |
| `coaching-rate`      | Amount of time spent training instead of working |  |
| `activity`           | Activity chosen for current tick                 |  |
| `revenue`            | Revenue of company for current tick              |  |
| `cumulative-revenue` | Overall revenue of company                       |  |
| `last-review`        | Tick count at last strategy review               |  |
| `developer-history` | List of developers that left the company, FIFO queue of size `developer-history-count` |  |
| `developers-leaving` | Number of developers that left in this tick |  |

**Global Variables**

| Name                  | Description                            |
|-----------------------|----------------------------------------|
| `ticks-per-year`        | Number of ticks in one year            |
| `turnovers-this-tick`   | Number of agents leaving a company     |
| `coaching-rate-options` | Coaching rates that companies can use  |
| `developer-history-count` | Maximum number of developers that left company to keep track of  |
| `market-mean-skill`     | Mean skill across all employed workers |
| `market-mean-revenue`   | Mean revenue across all companies      |

**Global Parameters**

| Name | Description |
|------------------------------|-------------------------------------------------------------------|
| `headcount-mean`               | Mean for headcount distribution                                   |
| `headcount-variance`           | Variance for headcount distribution                               |
| `hiring-threshold-mean`        | Mean for hiring threshold distribution                            |
| `hiring-threshold-variance`    | Variance for hiring threshold distribution                        |
| `diminishing-returns-coaching` | Enable diminishing returns when coaching                          |
| `coaching-skill-ceiling`       | Upper limit for skill level with diminished returns               |
| `coaching-skill-increase`      | Skill level increase when coaching                                |
| `working-skill-increase`       | Skill level increase when working                                 |
| `skill-decay`                  | Enable skill decay when no coaching happens                       |
| `skill-decay-threshold`        | Threshold after which decay starts                                |
| `skill-decay-rate`             | Rate at which skill decays per tick                               |
| `strategy-review-interval`     | Ticks between strategy reviews                                    |
| `dynamic-hiring-strategy`      | Enable changing hiring threshold when updating strategy           |
| `vacancy-rate-cutoff`          | Maximal allowed vacancy rate before hiring threshold is decreased |
| `hiring-threshold-ceiling`     | Upper limit for hiring threshold                                  |
| `dynamic-coaching-strategy`    | Enable changing the coaching rate when updating strategy          |
| `max-coaching-rate`            | Maximum allowed coaching rate                                     |
| `vacancy-rate-pressure`            | Enable coaching rate pressure from vacancy rate |
| `leaving-threshold`   | Value of `propensity-to-leave` at which developer changes company |
| `working-turnover-increase`    | Increase in turnover probability when working                     |
| `coaching-turnover-decrease`   | Decrease in turnover probability when coaching                    |


# Experiments

## Data Format

BehaviorSpace exports one row every tick. Each row has the following columns:

`"[all run data]","[step]","dependent-variables","skill-distribution","unemployment-rate"`

- **All run data**: empty (BehaviorSpace placeholder)
- **Step**: tick number
- **`dependent-variables`**: list of 4 sub-lists, one value per company (companies sorted by patch ID), produced by the `dependent-variables` reporter:
  - Index 0: Cumulative revenue
  - Index 1: Coaching rate (integer, ticks spent coaching out of `max-coaching-rate` options)
  - Index 2: Vacancies (`headcount`, current employee count)
  - Index 3: Mean propensity-to-leave of employees
- **`skill-distribution`**: list produced by the `skill-distribution` reporter:
  - Index 0: Mean skill level across all employed developers
  - Index 1: Standard deviation of skill level
  - Index 2: Median skill level
- **`unemployment-rate`**: fraction of all agents currently unemployed (0–1)

Example with three companies at tick 48:
```
,"48","[[138878 132572 125798] [5 3 7] [2 0 5] [12.3 8.5 15.1]]","[4424.652951096122 2340030.511432749 4430]","0.0016835016835016834"
```

## Sensitivity Analysis

All sensitivity experiments use: `repetitions=10`, `timeLimit=8000 ticks`, metrics collected every tick.

Reporters collected per run: `dependent-variables`, `skill-distribution`, `unemployment-rate`.

| Experiment name | IV | Tested values | Repetitions |
|---|---|---|---|
| `sensitivity-company-count` | `max-pxcor` / `max-pycor` | (3,3)=15 companies; (9,9)=99 companies; (13,13)=195 companies | 10 |
| `sensitivity-headcount` | `headcount-mean` | 30, 100 | 10 |
| `sensitivity-coaching-skill-ceiling` | `coaching-skill-ceiling` | 10000, 20000 | 10 |
| `sensitivity-coaching-skill-increase` | `coaching-skill-increase` | 20, 50 | 10 |
| `sensitivity-working-skill-increase` | `working-skill-increase` | 1, 2 | 10 |
| `sensitivity-skill-decay-rate` | `skill-decay-rate` | 0.1, 0.2, 0.3, 0.4, 0.5 | 10 |
| `sensitivity-leaving-threshold` | `leaving-threshold` | 25, 60 | 10 |
| `sensitivity-working-turnover-increase` | `working-turnover-increase` | 0.15, 0.30 | 10 |
| `sensitivity-coaching-turnover-decrease` | `coaching-turnover-decrease` | 1, 5 | 10 |
| `sensitivity-hiring-threshold-mean` | `hiring-threshold-mean` | 1000, 5000 | 10 |

The model contains **99 companies** (patches on a 10×10 grid, excluding patch 0 0 which serves as the unemployment pool) and a variable number of **developer agents** (turtles). Each tick corresponds to one working day; `ticks-per-year = 100`.

### Developers

| Model Parameter | Description | Baseline Value | Tested Values | Justification |
|---|---|---|---|---|
| Number of companies | The number of competing companies is fixed by the grid size (10×10 minus the unemployment patch at 0,0). | **TODO** | 15 (4×4), 99 (10×10), 195 (14×14) | Grid size determines the competitive landscape. Smaller grids reduce inter-company competition for talent; very large grids may dilute market-level effects. Outcomes such as mean skill and revenue should be evaluated relative to grid size to confirm robustness. |
| `headcount-mean` | Target number of developers per company, drawn from a normal distribution at initialization. | **TODO** | 30, 100 | A minimum headcount is required for coaching dynamics to emerge. At very low headcounts, individual departures cause disproportionate disruption. At very high headcounts, individual skill differences are averaged out. Baseline of 30 represents a mid-sized software team. |
| `headcount-variance` | Standard deviation of the headcount normal distribution across companies. | 10% | 10%  | A variance of 0 initializes all companies identically, isolating other effects. Increasing variance introduces heterogeneity in company size, reflecting real-world variation in team sizes. High variance may cause model degeneracy if some companies initialize with zero or negative headcount. |

### Coaching and Skill Dynamics

| Model Parameter | Description | Baseline Value | Tested Values | Justification |
|---|---|---|---|---|
| `diminishing-returns-coaching` (switch) | When ON, coaching skill gain follows exponential decay toward `coaching-skill-ceiling`: `Δskill = coaching-skill-increase × (1 − skill / ceiling)`. When OFF, skill increases linearly by `coaching-skill-increase` per coaching tick. | ON | ON | This switch determines whether coaching becomes less effective as developers approach the skill ceiling. With diminishing returns ON, companies face a strategic choice between investing in high-skill vs. low-skill developers. Comparing ON vs. OFF isolates this non-linearity. |
| `coaching-skill-ceiling` | Maximum skill level a developer can reach through coaching (skill points). Also acts as the cap for working skill increase. | **TODO** | 10'000, 20'000 | The ceiling defines the upper bound of the skill distribution. A low ceiling compresses the skill range, reducing the incentive to coach. A high ceiling allows large skill differentials, amplifying the tension between coaching investment and turnover risk. Must remain above realistic initial skill values (~7,200 for a 64-year-old developer). |
| `coaching-skill-increase` | Skill points added per coaching tick (before diminishing-returns adjustment if enabled). | **TODO** | 20, 50 | Controls the speed of human capital accumulation. Low values make coaching investment slow and potentially unattractive given turnover risk. High values make even short coaching sessions highly impactful, potentially destabilizing the market if developers quickly outgrow their company's hiring threshold. |
| `working-skill-increase` | Skill points added per working tick (capped at `coaching-skill-ceiling`). | **TODO** | 1, 2 | Represents on-the-job learning during productive work. A value of 0 means only coaching builds skill. A high value makes working almost as skill-building as coaching, reducing the incentive to invest in formal coaching sessions. |
| `skill-decay` (switch) | When ON, developer skill decays annually if the developer has not been coached within `skill-decay-threshold` ticks. | ON | ON | Skill decay motivates recurring coaching investment. Without decay, a single investment in coaching has permanent returns; with decay, coaching becomes an ongoing cost. This switch isolates whether the decay mechanism is necessary for observed long-run dynamics. |
| `skill-decay-threshold` | Number of ticks without coaching before skill decay begins. At `ticks-per-year = 100`, a threshold of 300 ticks equals 3 years. | 200 | 200 (2 yr) | A short threshold forces companies to coach frequently or risk skill erosion. A long threshold makes decay a background effect. The boundary at 100 ticks (1 year) tests whether annual coaching is required; at 800 ticks, decay becomes nearly irrelevant over a typical simulation run. |
| `skill-decay-rate` | Annual rate at which skill decays (applied per-tick as `rate / ticks-per-year`). A rate of 0.1 means 10% annual skill loss. | **TODO** | 0.05, 0.10 | Controls the severity of skill obsolescence. Low rates make decay a minor background effect; high rates force companies into aggressive coaching schedules or accept significant skill erosion. At 0.20, a developer losing no coaching for 5 years would retain only ~33% of their peak skill. |

### Turnover Behavior

| Model Parameter | Description | Baseline Value | Tested Values | Justification |
|---|---|---|---|---|
| `leaving-threshold` | Accumulated `propensity-to-leave` score at which a developer departs. Lower values make developers more sensitive to accumulated dissatisfaction. | **TODO** | 25, 60 | This threshold acts as the friction in the labor market. A low threshold produces high turnover even from moderate dissatisfaction. A high threshold means only severely dissatisfied developers leave, dampening turnover dynamics. Sensitivity tests confirm whether observed market equilibria are robust to this behavioral parameter. |
| `working-turnover-increase` | Increment added to `propensity-to-leave` each working tick. Represents accumulating dissatisfaction from stagnation during non-coaching periods. | **TODO** | 0.15, 0.30 | Controls the rate at which developers become dissatisfied during productive (non-coaching) periods. A value of 0 means working does not increase turnover propensity, eliminating the core tension of the model. A value of 0.50 means a developer reaches the baseline threshold of 25 after only 50 consecutive working ticks (~0.5 years). |
| `coaching-turnover-decrease` | Decrement subtracted from `propensity-to-leave` per coaching tick. Represents the retention benefit of investing in developers. | **TODO** | 1.00, 5.00 | Controls the effectiveness of coaching as a retention tool. At 0, coaching has no retention effect (only skill effect). At high values, a single coaching day can neutralize several working days of accumulated dissatisfaction, making coaching extremely powerful for retention. The ratio of `working-turnover-increase` to `coaching-turnover-decrease` determines the coaching-to-working balance needed to retain developers. |

### Company Strategy

| Model Parameter | Description | Baseline Value | Tested Values | Justification |
|---|---|---|---|---|
| `hiring-threshold-mean` | Mean minimum skill level (skill points) a candidate must exceed to be hired, drawn from a normal distribution at initialization. | **TODO** | 1'000, 5'000 | The hiring threshold determines initial selectivity in the labor market. A threshold of 1,700 sp corresponds roughly to a developer with 2–3 years of experience under the initial skill formula. Very low thresholds lead to rapid fill of vacancies at the cost of low initial team quality; very high thresholds risk persistent vacancies. |
| `hiring-threshold-variance` | Standard deviation of the hiring threshold normal distribution across companies at initialization. | 300 | 300 | Zero variance initializes all companies with identical thresholds; nonzero variance creates market niches (e.g., companies competing for different talent segments). High variance may lead some companies to initialize with thresholds exceeding the available labor pool, creating persistent vacancies from the start. |
| `hiring-threshold-ceiling` | Hard upper bound on hiring threshold when `dynamic-hiring-strategy` is ON. Prevents companies from raising thresholds arbitrarily high. | 15'000 sp | 15'000 sp | This ceiling constrains dynamic strategy adaptation. A low ceiling means all companies converge toward the same maximum selectivity. A ceiling close to `coaching-skill-ceiling` allows companies to hire only the most skilled developers available in the market, potentially leaving many vacancies unfilled. |
| `dynamic-hiring-strategy` (switch) | When ON, companies periodically adjust their `hiring-threshold` based on their current vacancy rate: lower the threshold if vacancy rate exceeds `vacancy-rate-cutoff`, raise it otherwise. | ON | ON | This switch enables adaptive company behavior. With OFF, hiring thresholds remain at their initialized values throughout the simulation. Comparing ON vs. OFF reveals whether strategic adaptation improves company performance and market stability, or whether it leads to emergent arms races or race-to-the-bottom dynamics. |
| `strategy-review-interval` | Number of ticks between strategy reviews (when `dynamic-hiring-strategy` is ON). | 50 ticks (0.5 years) | 50 | Controls how frequently companies can adapt their hiring strategy. Shorter intervals allow rapid adaptation but may cause oscillatory behavior. Longer intervals represent more inertial organizations. |
| `vacancy-rate-cutoff` | Vacancy rate threshold that triggers a hiring threshold reduction in the dynamic strategy. A rate above the cutoff means too many vacancies; the company lowers its bar to hire faster. | 0.05 (5%) | 0.05| This parameter sets the company's tolerance for understaffing. At 0.01, even a single vacancy in a 100-person team triggers a threshold reduction; at 0.40, companies accept 40% vacancy rates before relaxing hiring standards. Low cutoffs create aggressive downward pressure on hiring thresholds; high cutoffs let vacancies persist longer. |
| `max-coaching-rate` | Upper bound on initial coaching-rate assignment. Companies are initialized with a randomly chosen integer coaching rate in `[0, max-coaching-rate − 1]`, representing the percentage of ticks spent coaching. | 15 (uniform over 0–14%) | 15 | Sets the range of coaching intensity across companies at initialization. A lower maximum compresses companies toward low coaching rates, limiting heterogeneity in investment strategy. A value of 20 allows companies to initialize anywhere from 0% to 19% coaching rate, reflecting a broad range of investment philosophies. |
| `vacancy-rate-pressure` (switch) | When ON, companies that are understaffed (vacancy rate > 0) reduce their effective coaching rate proportionally to their vacancy rate: `effective-coaching-rate = coaching-rate × (1 − vacancy-rate)`. When OFF, coaching rate is applied regardless of staffing levels. | OFF | OFF | This switch captures the operational reality that understaffed teams cannot afford to take developers off productive work for coaching. With OFF, coaching rates are not affected by vacancies, testing whether observed dynamics depend on this constraint. Comparing ON vs. OFF reveals the interaction between staffing and training investment. |



This section summarises the sensitivity analysis performed on the model using NetLogo BehaviorSpace exports and the analysis notebook `sensitivity_analysis_batch_2.ipynb`.

Purpose
------------------

Assess how variation in key model parameters (IVs) affects model outputs (DVs). The analysis loads BehaviorSpace spreadsheet CSVs, extracts final-tick values per run, computes one-way effect sizes (η²), fits OLS regressions (slope, R², p-value) and produces per-experiment CSVs and plots as well as combined pivot tables and a heatmap.

How the batch works
-------------------
- Input: BehaviorSpace spreadsheet CSVs exported to `output/sensitivity-analysis/` (the notebook looks for files matching `*spreadh*eet*.csv`).
- For each CSV (one experiment / IV):
  1. Detect the IV and its human-readable label using `PARAM_LABEL_MAP`.
  2. Parse the final tick for every run and extract dependent variables.
  3. Compute η² across IV groups and run an OLS regression of each DV on the IV.
  4. Save per-experiment CSV and charts (η² bar chart and regression scatterplots).
- Aggregation: after all experiments are processed the notebook writes combined CSVs and pivot tables and saves a combined heatmap of η² + direction.

Dependent variables (DVs)
--------------------------

Extracted from the final tick of each run. Indices refer to positions in the corresponding NetLogo reporter list.

| Dependent variable | Source reporter | Index | Description |
|---|---|---|---|
| `cumulative_revenue` | `dependent-variables` | 0 | Firm cumulative revenue (mean across companies) |
| `coaching_rate` | `dependent-variables` | 1 | Coaching rate at final tick (mean across companies) |
| `vacancies` | `dependent-variables` | 2 | Open vacancies (mean across companies) |
| `propensity_to_leave` | `dependent-variables` | 3 | Mean propensity-to-leave of employees (mean across companies) |
| `skill_mean` | `skill-distribution` | 0 | Mean skill level across all employed developers |
| `unemployment_rate` | `unemployment-rate` | — | Fraction of all agents unemployed (enabled via `INCLUDE_UNEMPLOYMENT = True`) |

Key outputs produced
--------------------
- Per-experiment CSV: `output/output-effects/eta2_{experiment_stem}.csv` (η², slope, R², p, direction)
- Per-experiment charts: `output/output-effects/eta2_{experiment_stem}.png` and `output/output-effects/regression_{experiment_stem}.png`
- Combined CSVs / pivots:
  - `output/output-effects/eta2_all_experiments.csv`
  - `output/output-effects/eta2_pivot_all_experiments.csv` (η² pivot)
  - `output/output-effects/slope_pivot_all_experiments.csv`
  - `output/output-effects/direction_pivot_all_experiments.csv`
- Heatmap: `output/output-effects/eta2_heatmap_all_experiments.png`

Notes
-----
- The notebook expects BehaviorSpace spreadsheet CSV exports in `output/sensitivity-analysis/` and writes results to `output/output-effects/` (directory is created if missing).
- IV detection uses the `PARAM_LABEL_MAP` inside the notebook: add or modify map entries there to ensure experiment parameter names are converted to readable labels in charts and file names.
- Toggle `INCLUDE_UNEMPLOYMENT` in the notebook to include `unemployment_rate` as an analysed DV.
- CSV parsing constants (`PARAM_ROW = 8`, `DATA_START_ROW = 17`) are specific for the BehaviorSpace spreadsheet export format. Do not change unless the export format changes.

See `sensitivity_analysis_batch_2.ipynb` for implementation details and to inspect the exact loading/parsing logic used for BehaviorSpace spreadsheet exports.

## Comparison of Strategies

Experiment ideas:
- how often is a review done

To answer the initial research question, the simulation data is analyzed from different viewpoints to show the dependence of the DVs from the company choices.





# Credits
Developed by
- Güntensperger Raphael
- Ielpo Gianluca
- Schütz Michael
- Sutter Svenja
