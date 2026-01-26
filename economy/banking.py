"""
Banking & Financial System - Loans, Interest, and Debt

Implements:
- Banks and financial institutions
- Loans with interest rates
- Savings accounts with compound interest
- Debt collection and default
- Collateral and foreclosure
- Credit ratings
- Bank runs and failures
- Investment and speculation

Philosophy: Banking emerges when surplus wealth seeks returns.
Interest rates balance risk and reward.
Debt drives growth but creates instability.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum


class LoanType(Enum):
    """Types of loans"""
    PERSONAL = "personal"  # Personal consumption
    BUSINESS = "business"  # Business investment
    MORTGAGE = "mortgage"  # Property purchase
    EMERGENCY = "emergency"  # Crisis loan (high interest)


class LoanStatus(Enum):
    """Status of a loan"""
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    FORECLOSED = "foreclosed"


class CreditRating(Enum):
    """Credit worthiness of borrowers"""
    EXCELLENT = "excellent"  # AAA (2-5% interest)
    GOOD = "good"  # AA (5-10% interest)
    FAIR = "fair"  # A (10-20% interest)
    POOR = "poor"  # B (20-40% interest)
    VERY_POOR = "very_poor"  # C (40%+ interest or denied)


@dataclass
class Loan:
    """A loan from bank to borrower"""
    id: str
    bank_id: str
    borrower_id: str

    # Loan details
    loan_type: LoanType
    principal: float  # Original amount borrowed
    interest_rate: float  # Annual interest rate (0.05 = 5%)
    term_ticks: int  # How long to repay

    # Repayment
    amount_remaining: float  # How much left to pay
    payment_per_tick: float  # Regular payment amount
    ticks_remaining: int  # Ticks left to repay
    last_payment_tick: int = 0

    # Collateral (what can be seized if default)
    collateral: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: LoanStatus = LoanStatus.ACTIVE
    created_tick: int = 0
    defaulted_tick: int = 0

    # Payment history
    total_paid: float = 0.0
    missed_payments: int = 0


@dataclass
class SavingsAccount:
    """A savings account that earns interest"""
    id: str
    bank_id: str
    account_holder_id: str

    # Balance
    balance: float = 0.0
    interest_rate: float = 0.02  # 2% annual interest

    # History
    opened_tick: int = 0
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    interest_earned: float = 0.0

    # Status
    active: bool = True


@dataclass
class Bank:
    """A financial institution"""
    id: str
    name: str
    location: Tuple[float, float]

    # Ownership
    owner_id: str
    founded_tick: int

    # Capital
    reserves: float = 100.0  # Cash on hand
    assets: float = 0.0  # Value of loans outstanding
    deposits: float = 0.0  # Customer deposits

    # Interest rates
    savings_interest_rate: float = 0.02  # 2% APR for savers
    base_loan_interest_rate: float = 0.05  # 5% APR base for loans

    # Reserves ratio (regulatory)
    required_reserve_ratio: float = 0.10  # Must keep 10% of deposits as reserves

    # Loans and accounts
    active_loans: Set[str] = field(default_factory=set)
    savings_accounts: Set[str] = field(default_factory=set)

    # Risk management
    max_loan_amount: float = 1000.0
    credit_standards: float = 0.5  # 0-1, higher = stricter lending

    # Performance
    total_loans_issued: int = 0
    total_defaults: int = 0
    total_interest_earned: float = 0.0

    # Status
    operational: bool = True
    insolvent: bool = False


@dataclass
class Investment:
    """An investment/speculation"""
    id: str
    investor_id: str
    investment_type: str  # business, property, speculation, etc.

    # Investment details
    amount_invested: float
    expected_return_rate: float  # Expected % return
    actual_return_rate: float = 0.0  # Actual % return
    risk_level: float = 0.5  # 0-1, higher = riskier

    # Timeline
    invested_tick: int = 0
    maturity_ticks: int = 100
    realized_tick: int = 0

    # Status
    active: bool = True
    succeeded: bool = False


class BankingManager:
    """
    Manages the banking and financial system.

    Key mechanics:
    - Banks create money through fractional reserve lending
    - Interest rates balance supply and demand for capital
    - Credit ratings affect loan availability and rates
    - Defaults reduce bank capital and can cause failures
    - Bank runs occur when confidence collapses
    """

    def __init__(self):
        self.banks: Dict[str, Bank] = {}
        self.loans: Dict[str, Loan] = {}
        self.savings_accounts: Dict[str, SavingsAccount] = {}
        self.investments: Dict[str, Investment] = {}

        # Credit ratings
        self.credit_ratings: Dict[str, CreditRating] = {}

        # Statistics
        self.total_banks_founded: int = 0
        self.total_banks_failed: int = 0
        self.total_loans_issued: int = 0
        self.total_loan_value: float = 0.0
        self.total_defaults: int = 0
        self.total_interest_paid: float = 0.0

        # Economic indicators
        self.total_money_supply: float = 0.0  # Includes created credit
        self.average_interest_rate: float = 0.05

    # ===== BANK CREATION =====

    def found_bank(
        self,
        founder_id: str,
        location: Tuple[float, float],
        initial_capital: float,
        current_tick: int
    ) -> Bank:
        """Found a new bank"""

        bank_id = str(uuid.uuid4())

        bank = Bank(
            id=bank_id,
            name=f"{founder_id[:8]}'s Bank",
            location=location,
            owner_id=founder_id,
            founded_tick=current_tick,
            reserves=initial_capital
        )

        self.banks[bank_id] = bank
        self.total_banks_founded += 1

        return bank

    # ===== SAVINGS ACCOUNTS =====

    def open_savings_account(
        self,
        bank_id: str,
        account_holder_id: str,
        initial_deposit: float,
        current_tick: int
    ) -> Optional[SavingsAccount]:
        """Open a savings account"""

        if bank_id not in self.banks:
            return None

        bank = self.banks[bank_id]

        if not bank.operational:
            return None

        account_id = str(uuid.uuid4())

        account = SavingsAccount(
            id=account_id,
            bank_id=bank_id,
            account_holder_id=account_holder_id,
            balance=initial_deposit,
            interest_rate=bank.savings_interest_rate,
            opened_tick=current_tick,
            total_deposits=initial_deposit
        )

        self.savings_accounts[account_id] = account
        bank.savings_accounts.add(account_id)

        # Bank receives deposit
        bank.deposits += initial_deposit
        bank.reserves += initial_deposit

        return account

    def deposit(self, account_id: str, amount: float) -> bool:
        """Deposit money into savings account"""

        if account_id not in self.savings_accounts:
            return False

        account = self.savings_accounts[account_id]

        if not account.active:
            return False

        account.balance += amount
        account.total_deposits += amount

        # Add to bank reserves
        bank = self.banks.get(account.bank_id)
        if bank:
            bank.deposits += amount
            bank.reserves += amount

        return True

    def withdraw(self, account_id: str, amount: float) -> Tuple[bool, float]:
        """Withdraw money from savings account"""

        if account_id not in self.savings_accounts:
            return False, 0.0

        account = self.savings_accounts[account_id]

        if not account.active or amount > account.balance:
            return False, 0.0

        account.balance -= amount
        account.total_withdrawals += amount

        # Remove from bank reserves
        bank = self.banks.get(account.bank_id)
        if bank:
            bank.deposits -= amount
            bank.reserves -= amount

            # Check if bank has enough reserves
            if bank.reserves < 0:
                bank.insolvent = True
                return False, 0.0  # Bank run!

        return True, amount

    def apply_interest_to_savings(self, current_tick: int):
        """Apply interest to all savings accounts (compound interest)"""

        for account in self.savings_accounts.values():
            if not account.active:
                continue

            # Calculate interest (simplified: per-tick instead of annual)
            tick_interest_rate = account.interest_rate / 144  # 144 ticks per day
            interest = account.balance * tick_interest_rate

            account.balance += interest
            account.interest_earned += interest

            # Bank pays interest from reserves
            bank = self.banks.get(account.bank_id)
            if bank:
                bank.reserves -= interest

    # ===== LENDING =====

    def apply_for_loan(
        self,
        bank_id: str,
        borrower_id: str,
        amount: float,
        loan_type: LoanType,
        term_ticks: int,
        collateral: Dict,
        current_tick: int
    ) -> Dict:
        """Apply for a loan"""

        if bank_id not in self.banks:
            return {'approved': False, 'reason': 'Bank not found'}

        bank = self.banks[bank_id]

        if not bank.operational or bank.insolvent:
            return {'approved': False, 'reason': 'Bank not operational'}

        # Check if amount exceeds max
        if amount > bank.max_loan_amount:
            return {'approved': False, 'reason': f'Amount exceeds maximum ({bank.max_loan_amount})'}

        # Check reserve requirements
        required_reserves = bank.deposits * bank.required_reserve_ratio
        available_to_lend = bank.reserves - required_reserves

        if amount > available_to_lend:
            return {'approved': False, 'reason': 'Insufficient bank reserves'}

        # Credit check
        credit_rating = self.get_credit_rating(borrower_id)
        approval_chance = self._calculate_approval_chance(credit_rating, amount, collateral, bank.credit_standards)

        if random.random() > approval_chance:
            return {'approved': False, 'reason': 'Credit check failed'}

        # APPROVED! Calculate interest rate
        interest_rate = self._calculate_interest_rate(bank, credit_rating, loan_type)

        # Create loan
        loan_id = str(uuid.uuid4())

        # Calculate payment schedule
        # Simple: principal + interest divided by term
        total_to_repay = amount * (1 + interest_rate * (term_ticks / 144))
        payment_per_tick = total_to_repay / term_ticks

        loan = Loan(
            id=loan_id,
            bank_id=bank_id,
            borrower_id=borrower_id,
            loan_type=loan_type,
            principal=amount,
            interest_rate=interest_rate,
            term_ticks=term_ticks,
            amount_remaining=total_to_repay,
            payment_per_tick=payment_per_tick,
            ticks_remaining=term_ticks,
            collateral=collateral,
            created_tick=current_tick
        )

        self.loans[loan_id] = loan
        bank.active_loans.add(loan_id)

        # Bank accounting
        bank.reserves -= amount  # Give borrower the money
        bank.assets += total_to_repay  # Record loan as asset

        bank.total_loans_issued += 1

        self.total_loans_issued += 1
        self.total_loan_value += amount

        # Money creation! The loan created new money
        self.total_money_supply += amount

        return {
            'approved': True,
            'loan_id': loan_id,
            'amount': amount,
            'interest_rate': interest_rate,
            'payment_per_tick': payment_per_tick,
            'term_ticks': term_ticks,
            'total_to_repay': total_to_repay
        }

    def make_loan_payment(
        self,
        loan_id: str,
        payment_amount: float,
        current_tick: int
    ) -> Dict:
        """Make a payment on a loan"""

        if loan_id not in self.loans:
            return {'success': False, 'reason': 'Loan not found'}

        loan = self.loans[loan_id]

        if loan.status != LoanStatus.ACTIVE:
            return {'success': False, 'reason': 'Loan not active'}

        # Apply payment
        loan.amount_remaining -= payment_amount
        loan.total_paid += payment_amount
        loan.last_payment_tick = current_tick
        loan.ticks_remaining -= 1

        # Bank receives payment
        bank = self.banks.get(loan.bank_id)
        if bank:
            bank.reserves += payment_amount
            bank.assets -= payment_amount

            # Calculate interest portion
            interest_portion = payment_amount - (loan.principal / loan.term_ticks)
            if interest_portion > 0:
                bank.total_interest_earned += interest_portion
                self.total_interest_paid += interest_portion

        # Check if paid off
        if loan.amount_remaining <= 0 or loan.ticks_remaining <= 0:
            loan.status = LoanStatus.PAID_OFF
            bank.active_loans.discard(loan_id)

            # Improve credit rating
            self._improve_credit_rating(loan.borrower_id)

            return {
                'success': True,
                'paid_off': True,
                'message': 'Loan paid off!'
            }

        return {
            'success': True,
            'remaining': loan.amount_remaining,
            'ticks_left': loan.ticks_remaining
        }

    def check_for_defaults(self, current_tick: int) -> List[str]:
        """Check all loans for defaults"""

        defaulted_loans = []

        for loan in self.loans.values():
            if loan.status != LoanStatus.ACTIVE:
                continue

            # Check if payment is overdue
            ticks_since_payment = current_tick - loan.last_payment_tick
            if ticks_since_payment > 10:  # 10 ticks grace period
                loan.missed_payments += 1

            # Default after 3 missed payments
            if loan.missed_payments >= 3:
                self._default_loan(loan, current_tick)
                defaulted_loans.append(loan.id)

        return defaulted_loans

    def _default_loan(self, loan: Loan, current_tick: int):
        """Handle loan default"""

        loan.status = LoanStatus.DEFAULTED
        loan.defaulted_tick = current_tick

        bank = self.banks.get(loan.bank_id)
        if bank:
            # Bank loses the outstanding amount
            bank.assets -= loan.amount_remaining
            bank.total_defaults += 1

            # Check if bank becomes insolvent
            if bank.assets + bank.reserves < bank.deposits:
                bank.insolvent = True

        # Destroy credit rating
        self.credit_ratings[loan.borrower_id] = CreditRating.VERY_POOR

        self.total_defaults += 1

        # TODO: Seize collateral

    # ===== CREDIT RATINGS =====

    def get_credit_rating(self, agent_id: str) -> CreditRating:
        """Get agent's credit rating"""
        return self.credit_ratings.get(agent_id, CreditRating.FAIR)

    def _improve_credit_rating(self, agent_id: str):
        """Improve credit rating after successful repayment"""

        current = self.get_credit_rating(agent_id)

        rating_order = [
            CreditRating.VERY_POOR,
            CreditRating.POOR,
            CreditRating.FAIR,
            CreditRating.GOOD,
            CreditRating.EXCELLENT
        ]

        current_idx = rating_order.index(current)
        if current_idx < len(rating_order) - 1:
            self.credit_ratings[agent_id] = rating_order[current_idx + 1]

    def _calculate_approval_chance(
        self,
        credit_rating: CreditRating,
        amount: float,
        collateral: Dict,
        credit_standards: float
    ) -> float:
        """Calculate chance of loan approval"""

        base_chances = {
            CreditRating.EXCELLENT: 0.95,
            CreditRating.GOOD: 0.80,
            CreditRating.FAIR: 0.60,
            CreditRating.POOR: 0.30,
            CreditRating.VERY_POOR: 0.05
        }

        chance = base_chances.get(credit_rating, 0.5)

        # Adjust for collateral
        if collateral:
            chance += 0.2

        # Adjust for credit standards
        chance *= (1.0 - credit_standards * 0.3)

        return min(1.0, max(0.0, chance))

    def _calculate_interest_rate(
        self,
        bank: Bank,
        credit_rating: CreditRating,
        loan_type: LoanType
    ) -> float:
        """Calculate interest rate for loan"""

        # Base rate
        rate = bank.base_loan_interest_rate

        # Adjust for credit rating
        rating_adjustments = {
            CreditRating.EXCELLENT: 0.0,
            CreditRating.GOOD: 0.02,
            CreditRating.FAIR: 0.05,
            CreditRating.POOR: 0.15,
            CreditRating.VERY_POOR: 0.30
        }
        rate += rating_adjustments.get(credit_rating, 0.05)

        # Adjust for loan type
        type_adjustments = {
            LoanType.PERSONAL: 0.05,
            LoanType.BUSINESS: 0.0,
            LoanType.MORTGAGE: -0.02,
            LoanType.EMERGENCY: 0.20
        }
        rate += type_adjustments.get(loan_type, 0.0)

        return max(0.01, min(0.50, rate))  # 1% to 50%

    # ===== INVESTMENTS =====

    def create_investment(
        self,
        investor_id: str,
        amount: float,
        investment_type: str,
        expected_return: float,
        risk_level: float,
        maturity_ticks: int,
        current_tick: int
    ) -> Investment:
        """Create an investment"""

        investment_id = str(uuid.uuid4())

        investment = Investment(
            id=investment_id,
            investor_id=investor_id,
            investment_type=investment_type,
            amount_invested=amount,
            expected_return_rate=expected_return,
            risk_level=risk_level,
            invested_tick=current_tick,
            maturity_ticks=maturity_ticks
        )

        self.investments[investment_id] = investment

        return investment

    def realize_investment(
        self,
        investment_id: str,
        current_tick: int
    ) -> Dict:
        """Realize an investment (calculate actual return)"""

        if investment_id not in self.investments:
            return {'success': False, 'reason': 'Investment not found'}

        investment = self.investments[investment_id]

        # Calculate actual return (with variance based on risk)
        variance = investment.risk_level * 2.0  # Higher risk = higher variance
        actual_return = random.gauss(investment.expected_return_rate, variance)

        # Can lose money!
        actual_return = max(-1.0, actual_return)  # Can lose up to 100%

        investment.actual_return_rate = actual_return
        investment.realized_tick = current_tick
        investment.active = False
        investment.succeeded = actual_return > 0

        final_value = investment.amount_invested * (1 + actual_return)

        return {
            'success': True,
            'initial_investment': investment.amount_invested,
            'final_value': final_value,
            'profit_loss': final_value - investment.amount_invested,
            'return_rate': actual_return
        }

    # ===== QUERIES =====

    def get_agent_loans(self, agent_id: str) -> List[Loan]:
        """Get all loans for an agent"""
        return [l for l in self.loans.values() if l.borrower_id == agent_id]

    def get_agent_savings_accounts(self, agent_id: str) -> List[SavingsAccount]:
        """Get all savings accounts for an agent"""
        return [a for a in self.savings_accounts.values() if a.account_holder_id == agent_id]

    def get_total_debt(self, agent_id: str) -> float:
        """Get total outstanding debt for an agent"""
        return sum(l.amount_remaining for l in self.get_agent_loans(agent_id)
                  if l.status == LoanStatus.ACTIVE)

    def get_statistics(self) -> Dict:
        """Get banking statistics"""

        total_savings = sum(a.balance for a in self.savings_accounts.values())
        total_outstanding_loans = sum(l.amount_remaining for l in self.loans.values()
                                     if l.status == LoanStatus.ACTIVE)

        operational_banks = sum(1 for b in self.banks.values() if b.operational and not b.insolvent)

        return {
            'total_banks': len(self.banks),
            'operational_banks': operational_banks,
            'failed_banks': self.total_banks_failed,
            'total_loans_issued': self.total_loans_issued,
            'active_loans': sum(1 for l in self.loans.values() if l.status == LoanStatus.ACTIVE),
            'total_loan_value': round(self.total_loan_value, 2),
            'outstanding_debt': round(total_outstanding_loans, 2),
            'total_defaults': self.total_defaults,
            'default_rate': round((self.total_defaults / max(1, self.total_loans_issued)) * 100, 2),
            'total_savings': round(total_savings, 2),
            'savings_accounts': len(self.savings_accounts),
            'money_supply': round(self.total_money_supply, 2),
            'average_interest_rate': round(self.average_interest_rate * 100, 2)
        }
