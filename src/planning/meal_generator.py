class MealGenerator:
    def __init__(self):
        with open("data/meals.yml") as f:
            import yaml
            self.meals = yaml.safe_load(f)
    
    def generate_daily_plan(self, plan_json):
        menu = {"breakfast": [], "lunch": [], "dinner": [], "snacks": []}
        
        # BCMO1 example
        if any("BCMO1" in str(item) for item in plan_json["nutrition"]):
            menu["breakfast"].extend(self.meals["BCMO1"]["vitamin_a"]["breakfast"])
            menu["lunch"].extend(self.meals["BCMO1"]["vitamin_a"]["lunch"])
        
        # MCM6 lactose-free
        if any("MCM6" in str(item) for item in plan_json["nutrition"]):
            menu["breakfast"].extend(self.meals["MCM6"]["lactose_intolerant"]["breakfast"])
        
        return menu