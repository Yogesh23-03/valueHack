from .cascade import simulate

def compare_actions(delay: int):
    return {
        "do_nothing": simulate(delay=delay),
        "ask_extension": simulate(delay=delay, ext_a=15, ext_c=15),
        "early_discount": simulate(delay=delay, early_discount=0.02),
        "switch_vendor": simulate(delay=delay, alt_supplier=True, alt_fails=True),
        "combined": simulate(delay=delay, ext_c=15, early_discount=0.02)
    }
