"""
Fitness Calculations Helper Module

Handles BMR, TDEE, Macros, BMI, and Workout Volume parsing.
"""
import re

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI and return value, category, and trend (if applicable)."""
    if not weight_kg or not height_cm:
        return None, "N/A"
    
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
    
    if bmi < 18.5: category = "Underweight"
    elif 18.5 <= bmi < 24.9: category = "Normal weight"
    elif 25 <= bmi < 29.9: category = "Overweight"
    else: category = "Obese"
        
    return bmi, category

def calculate_bmr(weight_kg, height_cm, age_years, gender):
    """Calculate BMR using Mifflin-St Jeor Equation."""
    if not all([weight_kg, height_cm, age_years, gender]):
        return None
        
    # Mifflin-St Jeor
    try:
        base = (10 * float(weight_kg)) + (6.25 * float(height_cm)) - (5 * float(age_years))
        if str(gender).lower() == 'male':
            return round(base + 5)
        elif str(gender).lower() == 'female':
            return round(base - 161)
        else:
            return round(base - 78) # Average for other/unspecified
    except (ValueError, TypeError):
        return None

def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure."""
    if not bmr or not activity_level:
        return None
        
    multipliers = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extra active': 1.9,
        # Map common strings
        'low': 1.2,
        'medium': 1.55,
        'high': 1.725,
        'active': 1.55
    }
    
    activity_level = str(activity_level).lower()
    # Find closest match or default to moderately active
    multiplier = 1.55 
    for key, val in multipliers.items():
        if key in activity_level:
            multiplier = val
            break
            
    return round(bmr * multiplier)

def calculate_macro_targets(tdee, weight_kg, goal):
    """Calculate target calories and macros based on goal."""
    if not tdee or not weight_kg or not goal:
        return None
        
    goal = str(goal).lower()
    
    if 'fat loss' in goal or 'weight loss' in goal or 'lose' in goal:
        target_calories = tdee - 500
    elif 'muscle' in goal or 'gain' in goal or 'bulk' in goal:
        target_calories = tdee + 300
    else: # maintenance / recomp / strength
        target_calories = tdee

    try:
        weight_kg = float(weight_kg)
        # Bodybuilding standard macros
        # Protein: 2.2g per kg of bodyweight
        protein_g = round(weight_kg * 2.2)
        
        # Fat: 25% of target calories
        fat_cals = target_calories * 0.25
        fat_g = round(fat_cals / 9)
        
        # Carbs: Remainder of calories
        protein_cals = protein_g * 4
        carb_cals = target_calories - protein_cals - fat_cals
        carb_g = round(carb_cals / 4) if carb_cals > 0 else 0
        
        return {
            'target_calories': round(target_calories),
            'protein_g': protein_g,
            'fat_g': fat_g,
            'carb_g': carb_g,
            'fiber_g': 30 # General recommendation
        }
    except (ValueError, TypeError):
        return None

def parse_workout_volume(exercises_text):
    """
    Attempt to parse raw exercise text into total volume.
    Expected format examples:
    - Bench Press: 3x10x60kg
    - Squat: 4 sets of 8 reps @ 100 lbs
    Returns estimated total volume (rough estimation).
    """
    if not exercises_text:
        return 0
        
    total_volume = 0
    
    # Very basic regex to find patterns like number x number x number
    # E.g., 3x10x60 or 3 x 10 x 60
    patterns = [
        r'(\d+)\s*[x\*]\s*(\d+)\s*[x\*]\s*(\d+(?:\.\d+)?)', # 3x10x60
        r'(\d+)\s*sets.*?(\d+)\s*reps.*?(\d+(?:\.\d+)?)', # 3 sets of 10 reps @ 60
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, exercises_text, re.IGNORECASE)
        for match in matches:
            try:
                sets = float(match.group(1))
                reps = float(match.group(2))
                weight = float(match.group(3))
                total_volume += (sets * reps * weight)
            except ValueError:
                continue
                
    return total_volume
