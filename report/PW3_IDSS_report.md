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

## Knowledge-based Component

\[Describe the expert knowledge, rules, ontology, constraints, or other knowledge representation used. Identify its source and how it was elicited or constructed.\]

## Reasoning Mechanism

\[Explain how the system applies the knowledge: rule-based inference, case-based reasoning, qualitative reasoning, simulation, or another technique.\]

## Example Rules or Knowledge Structures

<div id="tab:rules">

| **ID** | **Condition (IF)** | **Conclusion / action (THEN)** |
|:-------|:-------------------|:-------------------------------|
| R1     | \[Condition\]      | \[Conclusion\]                 |
| R2     | \[Condition\]      | \[Conclusion\]                 |
| R3     | \[Condition\]      | \[Conclusion\]                 |

Example knowledge rules. Replace with rules actually used in the prototype.

</div>

## Interaction with Data-driven Models

\[Explain how the knowledge-based and data-driven components complement one another and contribute to the final decision support.\]

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
