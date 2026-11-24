<div class="titlepage">

UPC – URV – UB

Master in Artificial Intelligence

Intelligent Decision Support Systems

Fall semester \[YEAR\]

**Practical Work 3**

Building an Intelligent Decision Support System

**\[Full title of your IDSS project\]**

Team \[Team number\]

|                  |
|:----------------:|
| **Team members** |
|                  |
|                  |
|                  |
|                  |

\[Submission date\]

</div>

# Abstract

\[Write a concise summary of the problem domain, the decision-making problem, the proposed IDSS, the data and methods used, the main results, and the conclusions.\]

**Keywords:** Intelligent Decision Support System; \[domain\]; \[method\]; \[data-driven model\]; \[knowledge-based component\].

# Team Contributions

\[Briefly summarize how the work was coordinated and how the members contributed. The detailed task assignment and time sheet are provided in <a href="#ch:teamwork" data-reference-type="ref" data-reference="ch:teamwork">12</a>.\]

# Description of the Domain of Application

## Domain Overview

\[Describe the application domain, its context, relevant stakeholders, and why the problem matters.\]

## Problem Statement

\[Define the concrete problem addressed by the system. Explain the current situation and the limitations of existing decision-making processes.\]

## Objectives and Scope

- **General objective:** \[Main objective of the IDSS.\]

- **Specific objective 1:** \[Objective.\]

- **Specific objective 2:** \[Objective.\]

- **Scope and assumptions:** \[What is and is not covered.\]

## Available Data and Information

\[Summarize the available datasets, databases, expert knowledge, and any important data availability constraints.\]

# Main Identified Decisions

\[Identify the decisions that the system is intended to support. Explain who makes each decision, when it is made, what information is needed, and what the possible outcomes are.\]

<div id="tab:decisions">

| **ID** | **Decision**   | **Decision-maker** | **Information required / expected output** |
|:-------|:---------------|:-------------------|:-------------------------------------------|
| D1     | \[Decision 1\] | \[Actor\]          | \[Information and output\]                 |
| D2     | \[Decision 2\] | \[Actor\]          | \[Information and output\]                 |
| D3     | \[Decision 3\] | \[Actor\]          | \[Information and output\]                 |

Main decisions supported by the proposed IDSS.

</div>

# Functional Architecture of the IDSS Prototype

## System Actors and User Roles

\[Describe the types of users who interact with the system and their responsibilities.\]

<div id="tab:actors">

| **Actor** | **Responsibilities** | **System functionalities** |
|:----------|:---------------------|:---------------------------|
|           | \[Responsibilities\] | \[Functionalities\]        |
|           | \[Responsibilities\] | \[Functionalities\]        |
|           | \[Responsibilities\] | \[Functionalities\]        |

Actors, responsibilities, and functionalities.

</div>

## General Architecture

\[Explain how your design instantiates the general IDSS architecture presented in class. Describe the data, model, knowledge, inference, user-interface, and explanation components as applicable.\]

<figure id="fig:architecture">

<figcaption>Illustrative functional architecture. Replace or adapt the components and connections to match your implemented system.</figcaption>
</figure>

## Modules and Information Flow

\[Describe each module, its inputs and outputs, and how information flows between modules.\]

## Software Tools and Technologies

<div id="tab:tools">

| **Tool / language** | **Version** | **Purpose in the project**      |
|:--------------------|:------------|:--------------------------------|
|                     | \[Version\] | \[Data processing / modelling\] |
|                     | \[Version\] | \[Data storage\]                |
|                     | \[Version\] | \[User interface / deployment\] |

Software tools, languages, and their purpose.

</div>

# Data Pre-processing Summary

## Data Sources

\[Describe each raw dataset or database: source, URL or access details, variables, number of records, time period, and license if relevant.\]

## Data Understanding and Quality Assessment

\[Describe the exploratory analysis and quality issues found, such as missing values, duplicates, outliers, inconsistent formats, class imbalance, or noisy records.\]

## Pre-processing Pipeline

\[Explain the operations applied, why they were needed, and the order in which they were performed.\]

<figure id="fig:preprocessing">

<figcaption>Example data pre-processing pipeline. Adapt it to the actual workflow.</figcaption>
</figure>

## Final Dataset

\[Report the final dataset dimensions, selected features, target variable (if any), and any relevant changes after preprocessing.\]

<div id="tab:datasets">

| **Dataset**  | **Records** | **Features** | **Notes**                      |
|:-------------|:------------|:-------------|:-------------------------------|
| Raw          | \[N\]       | \[N\]        | \[Source / issues\]            |
| Preprocessed | \[N\]       | \[N\]        | \[Cleaning / transformations\] |
| Training     | \[N\]       | \[N\]        | \[Split details\]              |
| Testing      | \[N\]       | \[N\]        | \[Split details\]              |

Summary of datasets before and after preprocessing.

</div>

# Data-driven IDSS Models

## Modelling Objectives

\[Explain which decision-support tasks are addressed by data-driven modelling and why the selected approaches are appropriate.\]

## Model 1: \[Model name\]

### Method and Rationale

\[Describe the algorithm, its role in the IDSS, and why it was selected.\]

### Inputs, Outputs, and Configuration

\[Specify features, target, important hyperparameters, and output format.\]

### Training Procedure

\[Describe the training process, validation strategy, and software used.\]

### Results

\[Present relevant results using tables or figures. Explain what the results mean for the decisions supported.\]

<div id="tab:modelresults">

| **Metric** | **Value** |
|:-----------|:---------:|
|            | \[Value\] |
|            | \[Value\] |
|            | \[Value\] |

Example model evaluation results. Replace metrics with those appropriate to your task.

</div>

## Additional Models (if applicable)

\[Repeat the previous model structure for each additional model. Include descriptive, discriminant, predictive, or associative models as appropriate.\]

## Model Output and Integration

\[Explain how trained models are represented and used at system runtime. For example, describe how a trained decision tree is converted into machine-readable rules and evaluated on new cases.\]

# Data Post-processing and Model Validation

## Post-processing

\[Describe how model outputs are transformed into useful information for users, including ranking, thresholds, aggregation, formatting, or explanation.\]

## Validation Strategy

\[Describe the validation design, test data, baselines, metrics, and safeguards against data leakage.\]

## Validation Results

\[Present the validation results and interpret them in relation to the intended decisions.\]

## Limitations and Reliability

\[Discuss uncertainty, bias, generalizability, data limitations, and cases where recommendations should be reviewed by a human.\]

# Model-driven IDSS Techniques

The model-driven part of RentWise turns the renter's preferences and the price evidence into the Shortlist, Review, or Skip recommendation. It implements the personal-fit assessment and the recommendation described in the chapter *Main Identified Decisions*, and receives the price position from the data-driven component. All of its logic is contained in the Python package `rentwise`, and every numerical parameter is a named constant in `rentwise/config.py`. The values reported in this chapter are initial values chosen by the team; they have not been validated and are to be tuned during model validation.

## Knowledge-based Component

The knowledge represented in the component is of two kinds. The first is knowledge about the renter, elicited directly through the first decision: for each criterion that matters to them, the renter states a target value and a weight between 0 and 1, and a weight of 1.0 marks the criterion as non-negotiable. The criteria are limited to what the listings record: the monthly budget, the floor area, the numbers of bedrooms and bathrooms, the 27 amenities of the cleaned dataset (parking, pool, in-unit washer and dryer, and so on), and whether cats and dogs are allowed.

The second kind is domain knowledge, built by the team from the decision objectives, from multi-criteria decision analysis, and from the properties of the data. It consists of three structures:

- **Satisfaction functions** that express how far a listing satisfies each criterion, as a degree between 0 and 1. They encode the idea that a rent slightly above the budget, or a floor area slightly below the target, is a partial and not a complete failure.
- **Rules for missing information.** A criterion that the listing does not state, such as an unstated pet policy or a missing amenity list, is *unverifiable*: it is neither counted as satisfied nor as failed, but excluded from the score and reported to the renter. This follows directly from the two failure modes of the system: counting it as failed would sacrifice opportunity preservation, and counting it as satisfied would hide a real risk to financial protection.
- **Recommendation rules** that combine the personal fit, the veto of non-negotiable criteria, and the price position into a class, in the fixed order of precedence of the chapter *Main Identified Decisions*.

The listing and the preferences are represented as two simple data structures, `Listing` and `Preference`, so that the user interface and the later integration of the system share a single vocabulary of criteria. The criterion names are those of the cleaned dataset, for example `amenity_washer_dryer`.

## Reasoning Mechanism

The component reasons in three steps, matching the analysis and synthesis stages of the architecture. They are invoked through a single function, `assess(listing, preferences, price_assessor)`, which returns the class, the rule that decided it, the reasons, and the underlying personal-fit and price assessments.

**Evaluation of each criterion.** For every preference with a non-zero weight, the corresponding satisfaction function of Table "Satisfaction functions" is applied to the listing. The result is a degree *s<sub>i</sub>* in [0, 1], or *unknown* when the listing does not state the information.

**Aggregation with the Weighted Sum Model.** Let *V* be the set of criteria whose satisfaction is known and *w<sub>i</sub>* their weights. The personal-fit score is the weighted mean

*F* = Σ<sub>i∈V</sub> *w<sub>i</sub> s<sub>i</sub>* / Σ<sub>i∈V</sub> *w<sub>i</sub>*,

so the weights are renormalised over the verifiable criteria only, and *F* remains between 0 and 1 whatever the number of unknown criteria. When no weighted criterion is verifiable, the score is undefined. Each criterion's contribution is kept, so that the explanation can name the criteria that lowered the score most. In parallel, the veto is checked: a non-negotiable criterion whose satisfaction is known and lower than 1 is a veto. A non-negotiable criterion whose satisfaction is unknown is not a veto; it is passed to the rules as an open question.

**Rule-based classification.** The recommendation rules are evaluated in order, and the first rule whose condition holds determines the class. This forward, first-match inference makes the order of precedence explicit: a veto outweighs any price or fit evidence, firm negative evidence outweighs doubtful evidence, and a Shortlist is only issued when nothing calls for caution. Together with the class, the rules produce the explanation: the rule that fired and its conditions, the personal-fit score, the criteria that limited it with their degree of satisfaction, the criteria to ask the advertiser about, the gap between the asking rent and the reference, and the number of comparable listings behind it.

The asymmetry of the rules reflects the cost of the two errors. Skip is reached only through firm evidence: a verified failure of a non-negotiable criterion, a clearly insufficient fit, or a clear price gap supported by enough comparable listings. Every uncertain case falls through to Review.

## Example Rules or Knowledge Structures

The numerical criteria share the same shape: satisfaction is complete up to the target and decreases linearly to zero at the end of a tolerance band. The budget band is relative, because a gap of 100 USD matters more on a budget of 800 USD than on one of 3,000 USD; the floor-area band is relative for the same reason; the bedroom and bathroom bands are absolute, because these quantities take only a few discrete values.

<div id="tab:satisfaction">

| **Criterion** | **Satisfaction *s*** | **Parameter (initial value)** |
|:--|:--|:--|
| Budget | 1 if *x* ≤ *t*; 0 if *x* ≥ *t*(1+β); linear in between | β = 0.20 (`BUDGET_TOLERANCE`) |
| Floor area | 1 if *x* ≥ *t*; 0 if *x* ≤ *t*(1−α); linear in between | α = 0.25 (`SQUARE_FEET_TOLERANCE`) |
| Bedrooms | 1 if *x* ≥ *t*; 0 if *x* ≤ *t* − *b*; linear in between | *b* = 2 (`BEDROOMS_BAND`) |
| Bathrooms | 1 if *x* ≥ *t*; 0 if *x* ≤ *t* − *b*; linear in between | *b* = 1 (`BATHROOMS_BAND`) |
| Each amenity | 1 if listed, 0 if the amenity list omits it, unknown if the ad has no amenity list | — |
| Cats, dogs | 1 if allowed, 0 if not allowed, unknown if no pet policy is stated | — |

Satisfaction functions of the personal-fit assessment (*x*: value in the listing, *t*: renter's target). Parameter values are initial values, to be tuned during validation.

</div>

With these values, a rent 10% above the budget satisfies the budget to 0.5, a listing with one bedroom fewer than the target satisfies the bedroom criterion to 0.5, and a listing half a bathroom short satisfies the bathroom criterion to 0.5.

The price-position bands are applied to the relative gap *g* = (*x* − *r*) / *r* between the asking rent *x* and the reference rent *r*.

<div id="tab:parameters">

| **Parameter** | **Value** | **Meaning** |
|:--|:--|:--|
| `NON_NEGOTIABLE_WEIGHT` | 1.0 | Weight that marks a criterion as non-negotiable. |
| `FIT_VERY_LOW` | 0.40 | Below this score the personal fit is very low. |
| `FIT_GOOD` | 0.70 | From this score the fit is good; between the two thresholds it is intermediate. |
| `IN_LINE_BAND` | 0.10 | \|*g*\| ≤ 0.10: in line with the reference; *g* < −0.10: below it. |
| `MODERATE_BAND` | 0.25 | 0.10 < *g* ≤ 0.25: moderately above; *g* > 0.25: significantly above. |
| `MIN_COMPARABLES` | 10 | Minimum number of comparable listings for the evidence to be sufficient. |

Thresholds of the recommendation rules (initial values, to be tuned during validation).

</div>

The rules are evaluated from R1 to R4 and the first one that applies is used.

<div id="tab:rules">

| **ID** | **Condition (IF)** | **Conclusion (THEN)** |
|:-------|:-------------------|:----------------------|
| R1 | A non-negotiable criterion is verifiable and *s* < 1 (veto) | Skip |
| R2 | (the evidence is sufficient AND the position is significantly above the reference) OR *F* < `FIT_VERY_LOW` | Skip |
| R3 | A non-negotiable criterion is unverifiable OR the evidence is insufficient OR the position is moderately above the reference OR *F* < `FIT_GOOD` OR *F* is undefined | Review |
| R4 | Otherwise | Shortlist |

Recommendation rules of the prototype, in order of precedence.

</div>

Two properties of the rule base follow from its order. First, an unverifiable non-negotiable criterion can never lead to Skip by itself, since R1 only applies to verifiable criteria; the listing reaches R3 and the explanation names the criterion to ask the advertiser about. Second, insufficient comparable evidence can never lead to a price-based Skip, since R2 requires sufficient evidence; in that case no price position is issued at all, and the listing is sent to Review by R3 unless R1 or a very low fit already applies. The case of an undefined score, when none of the weighted criteria can be verified, is not covered explicitly in the chapter *Main Identified Decisions*; it is treated as a doubtful case and sent to Review. Each rule branch, the satisfaction functions at the limits of their bands, and these two properties are covered by automated tests in the repository.

## Interaction with Data-driven Models

The knowledge-based component does not estimate rents itself. It obtains the price position through a narrow interface, so that the data-driven model can be developed and replaced independently. Any object that provides a method `assess(listing)` returning a `PriceAssessment` can be used as price assessor. A `PriceAssessment` contains:

- the reference asking rent, in 2019 USD per month;
- the price position, one of *below*, *in line*, *moderately above*, or *significantly above*, or no position when the evidence is insufficient;
- the number of comparable listings behind the reference, and whether the evidence is sufficient for a judgement;
- the comparable listings themselves, which the interface shows to the renter as evidence.

The position is computed from the reference with the shared bands above, so that every price assessor applies the same definition of in line and overpriced. Deciding whether the evidence is sufficient is the responsibility of the price assessor, because it is the component that knows how reliable its estimate is; the rules only act on the flag.

Until the data-driven model is integrated, the prototype uses a simple placeholder assessor. It selects the historical listings with the same number of bedrooms, a number of bathrooms within 0.5, and a floor area within 25% of the listing, in the same city; when the city provides fewer than `MIN_COMPARABLES` such listings, the search is widened to the whole state, as a coarse form of the nearby areas mentioned in the chapter *Main Identified Decisions*. The reference rent is the median asking rent of the comparables. This placeholder is to be replaced by the K-nearest-neighbour retrieval and regression estimate of the data-driven chapter, without changes to the knowledge-based component.

The two components therefore complement each other. The data-driven model answers the question that does not depend on the renter, namely how the asking rent compares with the market of the data, and reports how much evidence supports that answer. The knowledge-based component answers the question that depends on the renter, combines both answers with explicit rules, and turns the uncertainty reported by the model into a Review rather than an unsupported Skip.

# Testing Use Cases

\[Describe at least three use cases that demonstrate how the IDSS supports different decision-making processes. Use realistic inputs and report the system outputs.\]

## Use Case 1: \[Name\]

**Goal:** \[What decision is being supported?\]  
**Actor:** \[Who uses the system?\]  
**Initial conditions:** \[Relevant context.\]  
**Input data:** \[Values or scenario.\]  
**Steps:**

1.  
2.  
3.  

**Expected output:** \[Expected recommendation or result.\]  
**Actual output:** \[Observed system result.\]  
**Assessment:** \[Did the system behave as expected? Explain.\]

## Use Case 2: \[Name\]

**Goal:** \[Goal.\]  
**Actor:** \[Actor.\]  
**Input data:** \[Scenario and inputs.\]  
**Steps:**

1.  
2.  
3.  

**Expected output:** \[Expected result.\]  
**Actual output:** \[Observed result.\]  
**Assessment:** \[Evaluation.\]

## Use Case 3: \[Name\]

**Goal:** \[Goal.\]  
**Actor:** \[Actor.\]  
**Input data:** \[Scenario and inputs.\]  
**Steps:**

1.  
2.  
3.  

**Expected output:** \[Expected result.\]  
**Actual output:** \[Observed result.\]  
**Assessment:** \[Evaluation.\]

## Use Case Comparison

<div id="tab:usecases">

| **Use case** | **Decision** | **Main input** | **Outcome** |
|:-------------|:-------------|:---------------|:------------|
| UC1          | \[Decision\] | \[Input\]      | \[Outcome\] |
| UC2          | \[Decision\] | \[Input\]      | \[Outcome\] |
| UC3          | \[Decision\] | \[Input\]      | \[Outcome\] |

Summary of the use cases tested.

</div>

# Global Evaluation of the IDSS and Conclusions

## System Performance

\[Evaluate the prototype in the designed scenarios. Discuss functional correctness, response time, usability, quality of recommendations, and other relevant performance dimensions.\]

## Achievement of Objectives

\[Review the objectives from <a href="#ch:domain" data-reference-type="ref" data-reference="ch:domain">1</a> and state which were achieved, partially achieved, or not achieved. Support the assessment with evidence.\]

## Strengths and Limitations

\[Summarize the main strengths and current limitations of the complete IDSS.\]

## Conclusions

\[Present the main conclusions from the development and evaluation of the prototype.\]

# Future Work and Improvements

\[Describe realistic next steps. Consider data quality and quantity, additional models, knowledge acquisition, explainability, user experience, security, deployment, and evaluation with real users where relevant.\]

- 
- 
- 

# Project Planning: Gantt Diagram

\[Explain the project phases, milestones, dependencies, and how the work was planned. Adapt the dates and tasks below.\]

<figure id="fig:gantt">
<div class="ganttchart">
<p><span>1</span><span>10</span><br />
<br />
<br />
<br />
<br />
<br />
<br />
<br />
<br />
<br />
<br />
<br />
</p>
</div>
<figcaption>Illustrative Gantt diagram. Update the timeline to reflect the team’s actual plan and execution.</figcaption>
</figure>

# Tasks Assignment and Team Responsibilities

\[Describe how responsibilities were distributed, how the team coordinated work, and how integration and review were handled.\]

<div id="tab:responsibilities">

| **Team member** | **Role** | **Assigned tasks and responsibilities** |
|:----------------|:---------|:----------------------------------------|
| **Team member** | **Role** | **Assigned tasks and responsibilities** |
|                 | \[Role\] | \[Tasks\]                               |
|                 | \[Role\] | \[Tasks\]                               |
|                 | \[Role\] | \[Tasks\]                               |
|                 | \[Role\] | \[Tasks\]                               |
|                 | \[Role\] | \[Tasks\]                               |

Task assignment and responsibilities.

</div>

# Team Time Sheet

\[Record the hours devoted by each team member to each task. Ensure the totals are consistent with the team’s accounting.\]

<div id="tab:timesheet">

| **Task**                  | **M1** | **M2** | **M3** | **M4** | **M5** |
|:--------------------------|:-------|:-------|:-------|:-------|:-------|
| **Task**                  | **M1** | **M2** | **M3** | **M4** | **M5** |
| Domain analysis           |        |        |        |        |        |
| Data collection           |        |        |        |        |        |
| Preprocessing             |        |        |        |        |        |
| Model development         |        |        |        |        |        |
| Knowledge component       |        |        |        |        |        |
| Interface and integration |        |        |        |        |        |
| Testing and evaluation    |        |        |        |        |        |
| Documentation and demo    |        |        |        |        |        |
| **Total hours**           |        |        |        |        |        |

Hours devoted by each team member to each task. Adapt the number of member columns to your team.

</div>

## Global Accounting per Team Member

<div id="tab:hours">

| **Team member** | **Total hours** |
|:----------------|:---------------:|
|                 |    \[Hours\]    |
|                 |    \[Hours\]    |
|                 |    \[Hours\]    |
|                 |    \[Hours\]    |
|                 |    \[Hours\]    |

Total hours per team member.

</div>

<div class="thebibliography">

99

\[Author or organization\], *\[Title of dataset, paper, documentation, or website\]*, \[Publisher / venue\], \[Year\]. Available: <a href="[URL]" class="uri">[URL]</a>. Accessed: \[date\].

\[Author\], “\[Title of article\],” *\[Journal or conference\]*, vol. \[x\], no. \[y\], pp. \[xx–yy\], \[year\].

</div>

# Additional Figures and Tables

\[Add supplementary plots, detailed metrics, screenshots, or tables that support the report but are not essential to the main narrative.\]

# Implementation Details

\[Add technical details, selected code excerpts, configuration information, or links to the project repository. Do not include large source files in the report; deliver source code in the required Source folder.\]

# README and Deliverable Structure

\[Briefly describe the contents of the final ZIP package and how to run the prototype/demo.\]
