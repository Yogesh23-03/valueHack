from sqlmodel import Session
from .db import engine, create_db_and_tables
from .models import Business, Supplier, Product, Customer

def seed_demo_data():
    create_db_and_tables()
    with Session(engine) as session:
        if session.query(Business).first():
            return
        
        b = Business(name="Sharma Hardware and Electricals", cash=50000, fixed_cost=3000, other_supplies=1800)
        session.add(b)
        session.commit()
        
        p1 = Product(name="fans", price=1900, cost=1400, demand_per_day=4, opening_stock=36, business_id=b.id)
        p2 = Product(name="wiring", price=1200, cost=900, demand_per_day=6, opening_stock=54, business_id=b.id)
        p3 = Product(name="switches", price=170, cost=95, demand_per_day=15, opening_stock=300, business_id=b.id)
        session.add_all([p1, p2, p3])
        
        s1 = Supplier(name="Supplier A", business_id=b.id)
        s2 = Supplier(name="Supplier C", business_id=b.id)
        s3 = Supplier(name="New Distributor", business_id=b.id)
        session.add_all([s1, s2, s3])
        
        c1 = Customer(name="Verma Contractors", business_id=b.id)
        session.add(c1)
        
        session.commit()

if __name__ == "__main__":
    seed_demo_data()
