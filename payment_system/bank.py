from payment_system.account import Account, CurrencyReserves
from utils.transaction import Transaction
from utils.currency import Currency
from utils.logger import LOGGER
from threading import Lock, Semaphore
from random import randint


class Bank():
    """
    Uma classe para representar um Banco.
    Se você adicionar novos atributos ou métodos, lembre-se de atualizar essa docstring.

    ...

    Atributos
    ---------
    _id : int
        Identificador do banco.
    currency : Currency
        Moeda corrente das contas bancárias do banco.
    reserves : CurrencyReserves
        Dataclass de contas bancárias contendo as reservas internas do banco.
    operating : bool
        Booleano que indica se o banco está em funcionamento ou não.
    accounts : List[Account]
        Lista contendo as contas bancárias dos clientes do banco.
    transaction_queue : Queue[Transaction]
        Fila FIFO contendo as transações bancárias pendentes que ainda serão processadas.
    national_transaction: int
        Quantidade de transações nacionais
    international_transaction: int
        Quantidade de transações internationais
    bank_taxes: int
        Quantidade de taxa por transferência internacional que o banco ganhou
    overdraft_taxes: int
        Quantidade de juros que o banco ganhou pelos clientes usarem o cheque especial

    Locks:
    - national_transaction_lock
    - international_transaction_lock
    - taxes_lock

    Semaphores:
    - semaphore_transaction_queue

    Métodos
    -------
    new_account(balance: int = 0, overdraft_limit: int = 0) -> None:
        Cria uma nova conta bancária (Account) no banco.
    new_transfer(origin: Tuple[int, int], destination: Tuple[int, int], amount: int, currency: Currency) -> None:
        Cria uma nova transação bancária.
    info() -> None:
        Printa informações e estatísticas sobre o funcionamento do banco.
    
    """

    def __init__(self, _id: int, currency: Currency):
        self._id                = _id
        self.currency           = currency
        self.reserves           = CurrencyReserves()
        self.operating          = True
        self.accounts           = [Account(_id=i, _bank_id=self._id, currency=self.currency, balance=randint(50_000_000, 300_000_000),
                                    overdraft_limit=randint(30_000_000, 100_000_000)) for i in range(101)]
        self.transaction_queue  = []

        self.bank_taxes = 0
        self.overdraft_taxes = 0

        self.taxes_lock = Lock()
    
        self.national_transaction = 0
        self.international_transaction = 0

        self.national_transaction_lock = Lock()
        self.international_transaction_lock = Lock()

        self.semaphore_transaction_queue = Semaphore(0)

    def new_account(self, balance: int = 0, overdraft_limit: int = 0) -> None:
        """
        Esse método deverá criar uma nova conta bancária (Account) no banco com determinado 
        saldo (balance) e limite de cheque especial (overdraft_limit).
        """
        # TODO: IMPLEMENTE AS MODIFICAÇÕES, SE NECESSÁRIAS, NESTE MÉTODO!

        # Gera _id para a nova Account
        acc_id = len(self.accounts) + 1

        # Cria instância da classe Account
        acc = Account(_id=acc_id, _bank_id=self._id, currency=self.currency, balance=balance, overdraft_limit=overdraft_limit)
  
        # Adiciona a Account criada na lista de contas do banco
        self.accounts.append(acc)


    def info(self) -> None:
        """
        Essa função deverá printar os seguintes dados utilizando o LOGGER fornecido:
        1. Saldo de cada moeda nas reservas internas do banco
        2. Número de transferências nacionais e internacionais realizadas
        3. Número de contas bancárias registradas no banco
        4. Saldo total de todas as contas bancárias (dos clientes) registradas no banco
        5. Lucro do banco: taxas de câmbio acumuladas + juros de cheque especial acumulados
        """
        # TODO: IMPLEMENTE AS MODIFICAÇÕES, SE NECESSÁRIAS, NESTE MÉTODO!

        LOGGER.info(f"\n\nEstatísticas do Banco Nacional {self._id}:")
        LOGGER.info(f"Saldo do Banco das seguintes moedas: ")
        LOGGER.info(f"USD -> {self.reserves.USD.balance:.2f}")
        LOGGER.info(f"EUR -> {self.reserves.EUR.balance:.2f}")
        LOGGER.info(f"GBP -> {self.reserves.GBP.balance:.2f}")
        LOGGER.info(f"JPY -> {self.reserves.JPY.balance:.2f}")
        LOGGER.info(f"CHF -> {self.reserves.CHF.balance:.2f}")
        LOGGER.info(f"BRL -> {self.reserves.BRL.balance:.2f}")

        LOGGER.info(f"Número de transferências nacionais -> {self.national_transaction}")
        LOGGER.info(f"Número de transferências nacionais -> {self.international_transaction}")

        LOGGER.info(f"Número de de contas bancárias registradas no banco -> {len(self.accounts)}")

        total = 0

        for account in self.accounts:
            total += account.balance

        LOGGER.info(f"Saldo total de todas as contas bancárias (dos clientes) registradas no banco -> {total:.2f}")
        LOGGER.info(f"Lucro do banco: {self.currency} {self.bank_taxes + self.overdraft_taxes:.2f}\n\n")
