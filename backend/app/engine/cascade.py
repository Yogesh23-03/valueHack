def simulate(delay=0, horizon=30, start_cash=50000, ext_a=0, ext_c=0, early_discount=0.0, alt_supplier=False, alt_fails=False, cost_spike_pct=0.0, customer_late_days=0) -> dict:
    stock = {"fans": 36, "wiring": 54, "switches": 300}
    demand = {"fans": 4, "wiring": 6, "switches": 15}
    price = {"fans": 1900, "wiring": 1200, "switches": 170}
    
    cash = start_cash
    fixed_cost = 3000 + 1800
    
    # Supplier A restock
    restock_day = 8 + delay
    if alt_supplier and not alt_fails:
        restock_day = 8 # assumed fast
    elif alt_supplier and alt_fails:
        restock_day = 999
        
    sup_a_due = 23 + ext_a
    sup_a_amount = 275000 * (1 - early_discount)
    if early_discount > 0:
        sup_a_due = 10
        
    # Supplier C
    sup_c_due = 25 + ext_c
    sup_c_amount = 70000
    
    # Customer Verma
    verma_qty = {"fans": 20, "wiring": 30}
    verma_amount = 20*1900 + 30*1200 # 74000
    
    stockout_day = None
    first_negative_day = None
    min_cash = cash
    failed = []
    delivered = False
    verma_delivery_day = None
    events = []
    
    cash_timeline = []
    stock_timeline = []
    
    for day in range(1, horizon + 1):
        # Restock
        if day == restock_day:
            stock["fans"] += 100
            stock["wiring"] += 150
            events.append({"day": day, "text": "Restock arrived"})
            
        # Deliver Verma
        if not delivered:
            if stock["fans"] >= verma_qty["fans"] and stock["wiring"] >= verma_qty["wiring"]:
                stock["fans"] -= verma_qty["fans"]
                stock["wiring"] -= verma_qty["wiring"]
                delivered = True
                verma_delivery_day = day
                events.append({"day": day, "text": "Delivered to Verma"})
                
        # Daily sales
        for item in ["fans", "wiring", "switches"]:
            if stock[item] >= demand[item]:
                stock[item] -= demand[item]
                cash += demand[item] * price[item]
            else:
                cash += stock[item] * price[item]
                stock[item] = 0
                if stockout_day is None:
                    stockout_day = day
                    events.append({"day": day, "text": f"Stockout on {item}"})
                    
        cash -= fixed_cost
        
        # Receivables
        if delivered and day == verma_delivery_day + 7 + customer_late_days:
            cash += verma_amount
            events.append({"day": day, "text": "Verma paid"})
            
        # Payables
        if day == sup_a_due:
            if cash >= sup_a_amount:
                cash -= sup_a_amount
            else:
                failed.append({"name": "Supplier A", "day": day})
                
        if day == sup_c_due:
            if cash >= sup_c_amount:
                cash -= sup_c_amount
            else:
                failed.append({"name": "Supplier C", "day": day})
                
        if cash < 0 and first_negative_day is None:
            first_negative_day = day
            events.append({"day": day, "text": "Cash went negative"})
            
        if cash < min_cash:
            min_cash = cash
            
        cash_timeline.append(cash)
        stock_timeline.append(stock.copy())
        
    return {
        "stockout": stockout_day,
        "lost_rev": 0,
        "first_negative_day": first_negative_day,
        "min_cash": min_cash,
        "min_day": 0,
        "failed": failed,
        "delivered": delivered,
        "end_cash": cash,
        "cash_timeline": cash_timeline,
        "stock_timeline": stock_timeline,
        "events": events
    }
