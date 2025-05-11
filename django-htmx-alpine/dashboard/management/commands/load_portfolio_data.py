import os
import csv
from django.core.management.base import BaseCommand, CommandError
from dashboard.models import Client, Account, Instrument, PositionSnapshot  # adjust app name as needed
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Loads portfolio data from a folder containing clients.csv, accounts.csv, instruments.csv, position_snapshots.csv'

    def add_arguments(self, parser):
        parser.add_argument('--data_folder', type=str, help='Path to folder containing the CSV files')

    def handle(self, *args, **options):
        self.folder = options['data_folder']
        self.log = lambda msg: self.stdout.write(self.style.NOTICE(msg))

        self.load_clients()
        self.load_accounts()
        self.load_instruments()
        self.load_position_snapshots()

        self.stdout.write(self.style.SUCCESS("Portfolio data loaded successfully."))

    def load_clients(self):
        client_file = os.path.join(self.folder, 'clients.csv')
        if not os.path.exists(client_file):
            raise CommandError(f"Missing file: {client_file}")

        self.log("Loading Clients...")
        new_clients = 0
        with open(client_file, newline='') as f:
            for row in csv.DictReader(f):
                obj, created = Client.objects.get_or_create(client_id=row['client_id'], defaults={'name': row['name']})
                if created:
                    new_clients += 1
        self.log(f"Loaded {new_clients} new clients.")

    def load_accounts(self):
        account_file = os.path.join(self.folder, 'accounts.csv')
        if not os.path.exists(account_file):
            raise CommandError(f"Missing file: {account_file}")

        self.log("Loading Accounts...")
        new_accounts = 0
        with open(account_file, newline='') as f:
            for row in csv.DictReader(f):
                client = Client.objects.get(client_id=row['client_id'])
                obj, created = Account.objects.get_or_create(
                    account_id=row['account_id'],
                    defaults={'client': client, 'account_name': row['account_name']}
                )
                if created:
                    new_accounts += 1
        self.log(f"Loaded {new_accounts} new accounts.")

    def load_instruments(self):
        instrument_file = os.path.join(self.folder, 'instruments.csv')
        if not os.path.exists(instrument_file):
            raise CommandError(f"Missing file: {instrument_file}")

        self.log("Loading Instruments...")
        new_instruments = 0
        with open(instrument_file, newline='') as f:
            for row in csv.DictReader(f):
                obj, created = Instrument.objects.get_or_create(symbol=row['symbol'], defaults={'name': row['name']})
                if created:
                    new_instruments += 1
        self.log(f"Loaded {new_instruments} new instruments.")

    def load_position_snapshots(self):
        position_file = os.path.join(self.folder, 'position_snapshots.csv')
        if not os.path.exists(position_file):
            raise CommandError(f"Missing file: {position_file}")

        self.log("Loading Position Snapshots...")
        snapshots = []
        total_rows = 0
        with open(position_file, newline='') as f:
            for row in csv.DictReader(f):
                total_rows += 1
                try:
                    account = Account.objects.get(account_id=row['account_id'])
                    instrument = Instrument.objects.get(symbol=row['symbol'])
                    date = datetime.strptime(row['Date'], "%Y-%m-%d").date()

                    snapshots.append(PositionSnapshot(
                        date=date,
                        account=account,
                        instrument=instrument,
                        units=Decimal(row['Units']),
                        market_price=Decimal(row['Market Price']),
                        market_value=Decimal(row['Market Value']),
                        book_value=Decimal(row['Book Value']),
                        deposits=Decimal(row['Deposits']),
                        withdrawals=Decimal(row['Withdrawals']),
                        net_deposits=Decimal(row['Net Deposits']),
                        total_return=Decimal(row['Total Return']),
                        cumulative_return=Decimal(row['Cumulative Return']),
                        pct_of_portfolio=Decimal(row['% of Portfolio'])
                    ))
                except Exception as e:
                    self.log(f"Error processing row {total_rows}: {e}")

        PositionSnapshot.objects.bulk_create(snapshots, batch_size=1000)
        self.log(f"Inserted {len(snapshots)} position snapshots.")
