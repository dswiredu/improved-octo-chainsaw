your_project/
│
├── data/                       # raw files live here
│   ├── Base_case.csv
│   └── curves.csv
│
├── configs/                    # expectation JSON per file
│   ├── base_case_expectations.json
│   └── curves_expectations.json
│
├── custom_checks/              # optional Python checks per file
│   └── base_case.py
│
├── outputs/                    # good / bad rows land here
├── reports/                    # html data-docs land here
│
└── run_validation.py           # master script (see step 4)
