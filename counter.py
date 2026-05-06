def counter_water_goal(kg):
    if not isinstance(kg, (int, float)):
        raise TypeError("Вес должен быть числом")
    if kg < 0:
        raise ValueError("Вес должен быть положительным числом")
    return kg * 30


def counter_water_liter(milliliter):
    if not isinstance(milliliter, (int, float)):
        raise TypeError("Миллилитры должны быть числом")
    if milliliter < 0:
        raise ValueError("Миллилитры должны быть положительным числом")
    return milliliter / 1000