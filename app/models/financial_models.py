from app import db
from datetime import datetime

class PLData(db.Model):
    __tablename__ = 'pl_data'
    
    id = db.Column(db.Integer, primary_key=True)
    account_code = db.Column(db.String(50))
    account_name = db.Column(db.String(200))
    period_month = db.Column(db.String(20))
    period_year = db.Column(db.Integer)
    amount = db.Column(db.Numeric(15, 2))
    percentage = db.Column(db.Numeric(5, 2))
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PLData {self.account_code} {self.period_month}/{self.period_year}: {self.amount}>'

class PayrollTrendsData(db.Model):
    __tablename__ = 'payroll_trends_data'
    
    id = db.Column(db.Integer, primary_key=True)
    week_ending = db.Column(db.Date)
    location_code = db.Column(db.String(20))
    rental_revenue = db.Column(db.Numeric(15, 2))
    all_revenue = db.Column(db.Numeric(15, 2))
    payroll_amount = db.Column(db.Numeric(15, 2))
    wage_hours = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PayrollTrendsData {self.location_code} {self.week_ending}: Rev={self.rental_revenue}, Payroll={self.payroll_amount}>'

class ScorecardTrendsData(db.Model):
    __tablename__ = 'scorecard_trends_data'
    
    id = db.Column(db.Integer, primary_key=True)
    week_ending = db.Column(db.Date)
    total_weekly_revenue = db.Column(db.Numeric(15, 2))
    revenue_3607 = db.Column(db.Numeric(15, 2))
    revenue_6800 = db.Column(db.Numeric(15, 2))
    revenue_728 = db.Column(db.Numeric(15, 2))
    revenue_8101 = db.Column(db.Numeric(15, 2))
    new_contracts_3607 = db.Column(db.Integer)
    new_contracts_6800 = db.Column(db.Integer)
    new_contracts_728 = db.Column(db.Integer)
    new_contracts_8101 = db.Column(db.Integer)
    deliveries_scheduled_8101 = db.Column(db.Integer)
    reservation_next14_3607 = db.Column(db.Numeric(15, 2))
    reservation_next14_6800 = db.Column(db.Numeric(15, 2))
    reservation_next14_728 = db.Column(db.Numeric(15, 2))
    reservation_next14_8101 = db.Column(db.Numeric(15, 2))
    total_reservation_3607 = db.Column(db.Numeric(15, 2))
    total_reservation_6800 = db.Column(db.Numeric(15, 2))
    total_reservation_728 = db.Column(db.Numeric(15, 2))
    total_reservation_8101 = db.Column(db.Numeric(15, 2))
    ar_over_45_days_percent = db.Column(db.Numeric(5, 2))
    total_discount = db.Column(db.Numeric(15, 2))
    week_number = db.Column(db.Integer)
    open_quotes_8101 = db.Column(db.Integer)
    total_ar_cash_customers = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScorecardTrendsData {self.week_ending}: Total Rev={self.total_weekly_revenue}>'