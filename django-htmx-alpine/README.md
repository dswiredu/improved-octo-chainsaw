# Django + Alpine + HTMX + Daisy UI(Pines UI) + Plotly project
- Built off of stock market crash analysis here:[text](https://thecleverprogrammer.com/2025/04/01/stock-market-crash-analysis-with-python/)

To setup:
1. Create virtual environment : python -m venv .venv
2. Activate virtualenvitonment : .venv\bin\activate.ps1
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py createsuperuser
6. upload prices from crash analysis file: python manage.py load_historical_price --file_path path_to_file
7. python manage.py runserver
