import time
from threading import Thread

from globals import *
from payment_system.bank import Bank
from utils.transaction import Transaction, TransactionStatus
from utils.logger import LOGGER
from utils.currency import *

class PaymentProcessor(Thread):
    """
    Uma classe para representar um processador de pagamentos de um banco.
    Se você adicionar novos atributos ou métodos, lembre-se de atualizar essa docstring.

    ...

    Atributos
    ---------
    _id : int
        Identificador do processador de pagamentos.
    bank: Bank
        Banco sob o qual o processador de pagamentos operará.

    Métodos
    -------
    run():
        Inicia thread to PaymentProcessor
    process_transaction(transaction: Transaction) -> TransactionStatus:
        Processa uma transação bancária.
    """

    def __init__(self, _id: int, bank: Bank):
        Thread.__init__(self)
        self._id  = _id
        self.bank = bank


    def run(self):
        """
        Esse método deve buscar Transactions na fila de transações do banco e processá-las 
        utilizando o método self.process_transaction(self, transaction: Transaction).
        Ele não deve ser finalizado prematuramente (antes do banco realmente fechar).
        """
        # TODO: IMPLEMENTE/MODIFIQUE O CÓDIGO NECESSÁRIO ABAIXO !

        LOGGER.info(f"Inicializado o PaymentProcessor {self._id} do Banco {self.bank._id}!")
        queue = banks[self.bank._id].transaction_queue

        while banks[self.bank._id].operating:
            banks[self.bank._id].semaphore_transaction_queue.acquire()

            transaction = queue.pop(0)
            #LOGGER.info(f"Transaction_queue do Banco {self.bank._id}: {queue}")
            self.process_transaction(transaction)

            time.sleep(3 * time_unit)  # Remova esse sleep após implementar sua solução!

        LOGGER.info(f"O PaymentProcessor {self._id} do banco {self.bank._id} foi finalizado.")


    def process_transaction(self, transaction: Transaction) -> TransactionStatus:
        """
        Esse método deverá processar as transações bancárias do banco ao qual foi designado.
        Caso a transferência seja realizada para um banco diferente (em moeda diferente), a 
        lógica para transações internacionais detalhada no enunciado (README.md) deverá ser
        aplicada.
        Ela deve retornar o status da transacão processada.
        """
        # Pablo - Implementação do código da função process_transaction() 

        LOGGER.info(f"PaymentProcessor {self._id} do Banco {self.bank._id} iniciando processamento da Transaction {transaction._id}!")
        
        # Caso a transação seja feita entre bancos diferentes (moedas diferentes também)
        if self.bank._id != transaction.destination[0]:
            with self.bank.international_transaction_lock:
                self.bank.international_transaction += 1
            transaction_withdraw: int
    
            rate = get_exchange_rate(self.bank.currency, transaction.currency)
            banco_origem = banks[transaction.origin[0]]
            cliente_origem = banco_origem.accounts[transaction.origin[1]]
            (successfull, overdraft_used, amount_overdraft) = cliente_origem.withdraw(transaction.amount)
            
            if successfull:
                if overdraft_used:
                    transaction_withdraw = (transaction.amount - amount_overdraft + amount_overdraft * 0.95) * rate * 0.99
                    with self.bank.taxes_lock:
                        self.bank.bank_taxes += (transaction.amount - amount_overdraft + amount_overdraft * 0.95) * 0.01
                        self.bank.overdraft_taxes += amount_overdraft * 0.05
                else:
                    transaction_withdraw = (transaction.amount * rate) * 0.99
                    with self.bank.taxes_lock:
                        self.bank.bank_taxes += (transaction.amount * rate) * 0.01

                #Depositando moeda de uma conta para a outra
                match transaction.currency:
                    case Currency.USD:
                        self.bank.reserves.USD.deposit(rate * transaction.amount)
                        self.bank.reserves.USD.withdraw(transaction_withdraw)

                    case Currency.EUR:
                        self.bank.reserves.EUR.deposit(rate * transaction.amount)
                        self.bank.reserves.EUR.withdraw(transaction_withdraw)

                    case Currency.GBP:
                        self.bank.reserves.GBP.deposit(rate * transaction.amount)
                        self.bank.reserves.GBP.withdraw(transaction_withdraw)

                    case Currency.JPY:
                        self.bank.reserves.JPY.deposit(rate * transaction.amount)
                        self.bank.reserves.JPY.withdraw(transaction_withdraw)

                    case Currency.CHF:
                        self.bank.reserves.CHF.deposit(rate * transaction.amount)
                        self.bank.reserves.CHF.withdraw(transaction_withdraw)

                    case _:
                        self.bank.reserves.BRL.deposit(rate * transaction.amount)
                        self.bank.reserves.BRL.withdraw(transaction_withdraw)

                banco_destino = banks[transaction.destination[0]]
                cliente_destino = banco_destino.accounts[transaction.destination[1]]    
                cliente_destino.deposit(transaction_withdraw)
        
        # Caso a transação seja feita entre contas do mesmo banco
        else:
            with self.bank.national_transaction_lock:
                self.bank.national_transaction += 1

    
            banco = banks[transaction.origin[0]]
            cliente_origem = banco.accounts[transaction.origin[1]]
            (successfull, overdraft_used, amount_overdraft) = cliente_origem.withdraw(transaction.amount)

            transaction_final: int

            if overdraft_used:
                transaction_final = (transaction.amount - amount_overdraft + amount_overdraft * 0.95)
                with self.bank.taxes_lock:
                    self.bank.overdraft_taxes += amount_overdraft * 0.05
            else:
                transaction_final = transaction.amount
            
            cliente_destino = banco.accounts[transaction.destination[1]]
            cliente_destino.deposit(transaction_final)

        # NÃO REMOVA ESSE SLEEP!
        # Ele simula uma latência de processamento para a transação.
        time.sleep(3 * time_unit)

        transaction.set_status(TransactionStatus.SUCCESSFUL)

        self.bank.transaction_interval_lock.acquire()
        self.bank.transaction_interval['transactions_amt'] += 1
        self.bank.transaction_interval['total_time'] += transaction.get_processing_time().total_seconds()
        self.bank.transaction_interval_lock.release()
        return transaction.status
