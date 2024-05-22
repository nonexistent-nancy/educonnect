"""
Transaction Handler

This module contains the TransactionHandler class, which is responsible for
handling transactions.

A Transaction is any change performed on the database. This includes
inserting, updating, and deleting records, assigning grades, and so on.

The TransactionHandler class is responsible for handling these transactions
and ensuring that they are performed correctly.

For Logging, every transaction is logged in the database. This log contains
the following information:
    - The User who performed the transaction
    - The Time the transaction was performed
    - A Label for the transaction
    - The Before state of the record
    - The After state of the record

This allows for easy debugging and auditing of the database.
Objects such as the TransactionInterpreter can use this information to
determine what changes were made to the database and notify all affected parties.

A User can also view all transactions that have been made to the database that affect them.
This allows for transparency and accountability, further ensuring the integrity of the database.

Any affected Party has the right to dispute a transaction. This dispute will be logged in the database and will be
reviewed by an Administrator, as well as internal systems, to determine the validity of the dispute.

The TransactionDisputeHandler class is responsible for handling these disputes and ensuring that they are resolved in a
timely manner.
"""

from datetime import datetime
from utils.signal import perform_transactions

class Transaction:
    def __init__(self, user, label, before, after):
        self.user = user
        self.label = label
        self.before = before
        self.after = after
        self.timestamp = datetime.now()
        self.disputed = False

    def dispute(self):
        self.disputed = True

class TransactionHandler:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def perform_transactions(self):
        for transaction in self.transactions:
            if transaction.disputed:
                perform_transactions.emit("dispute_transaction", transaction)
            else:
                perform_transactions.emit("perform_transactions", transaction) # Emit signal to aacs and other systems
            