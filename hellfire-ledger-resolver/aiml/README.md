# AIML Module – Debt Settlement Optimizer

This module optimizes financial settlements between multiple participants by minimizing the number of transactions required.

## Workflow

CSV Data → Data Cleaning → Transaction Generation → Debt Optimization → JSON Output

## Files

app.py
Main runner that connects all modules and outputs settlement results in JSON format.

cleaning.py
Handles dataset loading and cleaning.

optimizer.py
Implements the core debt minimization algorithm.

utils.py
Contains helper functions such as transaction generation.

schema.py
Defines the settlement data structure.

tests/test_optimizer.py
Unit test that verifies correctness of the optimization algorithm.

## How to Run

Run the module:

python app.py

Run tests:

python tests/test_optimizer.py
