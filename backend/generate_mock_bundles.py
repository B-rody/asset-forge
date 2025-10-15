"""
Generate Mock Bundles for Testing Packager
Creates realistic bundle folders with assets, ready for packaging
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.settings import settings
from app.database import DatabaseManager
from app.database.queries import BundleQueries, IdeaQueries
from app.database.models import Bundle, Idea

# Mock bundle configurations
MOCK_BUNDLES = [
    {
        "title": "Weekly Habit Tracker Bundle",
        "niche": "Productivity & Self-Development",
        "sub_niche": "Habit formation tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Weekly Habit Tracker",
                "description": "A comprehensive weekly tracking tool with daily habit checkboxes, goal-setting sections, and progress visualization.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_weekly-habit-tracker.md",
                "content": """# Weekly Habit Tracker

## Daily Habits
Track your daily habits with ease!

### Monday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Tuesday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Wednesday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Thursday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Friday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Saturday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

### Sunday
- [ ] Exercise
- [ ] Meditation
- [ ] Reading
- [ ] Healthy Eating
- [ ] Water Intake (8 glasses)

## Weekly Summary
Reflect on your week and plan for the next one.

**This week's wins:**
_________________________________

**Areas to improve:**
_________________________________

**Next week's goals:**
_________________________________
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Monthly Goals Planner",
                "description": "A monthly planning template with goal-setting frameworks and progress tracking.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_monthly-goals-planner.md",
                "content": """# Monthly Goals Planner

## Goals for This Month

### Career Goals
1. _________________________________
2. _________________________________
3. _________________________________

### Health & Fitness Goals
1. _________________________________
2. _________________________________
3. _________________________________

### Personal Development Goals
1. _________________________________
2. _________________________________
3. _________________________________

### Relationship Goals
1. _________________________________
2. _________________________________
3. _________________________________

## Weekly Breakdown

### Week 1 Focus:
_________________________________

### Week 2 Focus:
_________________________________

### Week 3 Focus:
_________________________________

### Week 4 Focus:
_________________________________

## Progress Tracking

**Milestones Achieved:**
- [ ] _________________________________
- [ ] _________________________________
- [ ] _________________________________

**Challenges Faced:**
_________________________________

**Lessons Learned:**
_________________________________
"""
            }
        ]
    },
    {
        "title": "Budget Planner & Finance Tracker Bundle",
        "niche": "Personal Finance",
        "sub_niche": "Budget management tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Monthly Budget Worksheet",
                "description": "A detailed monthly budget tracker with income, expenses, and savings categories.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_monthly-budget-worksheet.md",
                "content": """# Monthly Budget Worksheet

## Income
| Source | Amount |
|--------|--------|
| Salary | $______ |
| Side Income | $______ |
| Investments | $______ |
| Other | $______ |
| **Total Income** | **$______** |

## Fixed Expenses
| Category | Amount |
|----------|--------|
| Rent/Mortgage | $______ |
| Utilities | $______ |
| Insurance | $______ |
| Subscriptions | $______ |
| Loan Payments | $______ |
| **Total Fixed** | **$______** |

## Variable Expenses
| Category | Amount |
|----------|--------|
| Groceries | $______ |
| Dining Out | $______ |
| Transportation | $______ |
| Entertainment | $______ |
| Shopping | $______ |
| **Total Variable** | **$______** |

## Savings & Investments
| Goal | Amount |
|------|--------|
| Emergency Fund | $______ |
| Retirement | $______ |
| Vacation | $______ |
| Other Goals | $______ |
| **Total Savings** | **$______** |

## Summary
- **Total Income:** $______
- **Total Expenses:** $______
- **Total Savings:** $______
- **Balance:** $______
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Expense Tracker Log",
                "description": "Daily expense tracking template to monitor spending habits.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_expense-tracker-log.md",
                "content": """# Daily Expense Tracker

## Week 1

### Monday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Tuesday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Wednesday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Thursday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Friday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Saturday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

### Sunday
| Time | Category | Description | Amount |
|------|----------|-------------|--------|
| __:__ | ________ | ___________ | $_____ |
| __:__ | ________ | ___________ | $_____ |
| **Daily Total** | | | **$_____** |

## Weekly Total: $______
"""
            },
            {
                "asset_id": "asset-003",
                "name": "Savings Goals Tracker",
                "description": "Visual progress tracker for multiple savings goals.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-003_savings-goals-tracker.md",
                "content": """# Savings Goals Tracker

## Goal 1: Emergency Fund
**Target Amount:** $______
**Current Amount:** $______
**Deadline:** ___/___/___

Progress: ▢▢▢▢▢▢▢▢▢▢ (0%)

**Monthly Contribution:** $______

## Goal 2: Vacation Fund
**Target Amount:** $______
**Current Amount:** $______
**Deadline:** ___/___/___

Progress: ▢▢▢▢▢▢▢▢▢▢ (0%)

**Monthly Contribution:** $______

## Goal 3: Down Payment
**Target Amount:** $______
**Current Amount:** $______
**Deadline:** ___/___/___

Progress: ▢▢▢▢▢▢▢▢▢▢ (0%)

**Monthly Contribution:** $______

## Goal 4: Custom Goal
**Target Amount:** $______
**Current Amount:** $______
**Deadline:** ___/___/___

Progress: ▢▢▢▢▢▢▢▢▢▢ (0%)

**Monthly Contribution:** $______

## Total Savings Summary
- **Total Target:** $______
- **Total Saved:** $______
- **Remaining:** $______
- **Monthly Savings Rate:** $______
"""
            }
        ]
    },
    {
        "title": "Content Creator Planner Bundle",
        "niche": "Social Media & Content Creation",
        "sub_niche": "Content planning tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "30-Day Content Calendar",
                "description": "A comprehensive monthly content calendar with post ideas, scheduling, and analytics tracking.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_30-day-content-calendar.md",
                "content": """# 30-Day Content Calendar

## Month: _____________ Year: _______

### Week 1
| Day | Platform | Content Type | Topic | Status | Engagement |
|-----|----------|--------------|-------|--------|------------|
| Mon | ________ | ____________ | _____ | ☐ | __________ |
| Tue | ________ | ____________ | _____ | ☐ | __________ |
| Wed | ________ | ____________ | _____ | ☐ | __________ |
| Thu | ________ | ____________ | _____ | ☐ | __________ |
| Fri | ________ | ____________ | _____ | ☐ | __________ |
| Sat | ________ | ____________ | _____ | ☐ | __________ |
| Sun | ________ | ____________ | _____ | ☐ | __________ |

### Week 2
| Day | Platform | Content Type | Topic | Status | Engagement |
|-----|----------|--------------|-------|--------|------------|
| Mon | ________ | ____________ | _____ | ☐ | __________ |
| Tue | ________ | ____________ | _____ | ☐ | __________ |
| Wed | ________ | ____________ | _____ | ☐ | __________ |
| Thu | ________ | ____________ | _____ | ☐ | __________ |
| Fri | ________ | ____________ | _____ | ☐ | __________ |
| Sat | ________ | ____________ | _____ | ☐ | __________ |
| Sun | ________ | ____________ | _____ | ☐ | __________ |

### Week 3
| Day | Platform | Content Type | Topic | Status | Engagement |
|-----|----------|--------------|-------|--------|------------|
| Mon | ________ | ____________ | _____ | ☐ | __________ |
| Tue | ________ | ____________ | _____ | ☐ | __________ |
| Wed | ________ | ____________ | _____ | ☐ | __________ |
| Thu | ________ | ____________ | _____ | ☐ | __________ |
| Fri | ________ | ____________ | _____ | ☐ | __________ |
| Sat | ________ | ____________ | _____ | ☐ | __________ |
| Sun | ________ | ____________ | _____ | ☐ | __________ |

### Week 4
| Day | Platform | Content Type | Topic | Status | Engagement |
|-----|----------|--------------|-------|--------|------------|
| Mon | ________ | ____________ | _____ | ☐ | __________ |
| Tue | ________ | ____________ | _____ | ☐ | __________ |
| Wed | ________ | ____________ | _____ | ☐ | __________ |
| Thu | ________ | ____________ | _____ | ☐ | __________ |
| Fri | ________ | ____________ | _____ | ☐ | __________ |
| Sat | ________ | ____________ | _____ | ☐ | __________ |
| Sun | ________ | ____________ | _____ | ☐ | __________ |

## Monthly Analytics
- **Total Posts:** _____
- **Best Performing Post:** _____________________
- **Top Platform:** _____________________
- **Total Engagement:** _____
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Content Ideas Brainstorm Sheet",
                "description": "A creative brainstorming template for generating content ideas across multiple platforms.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_content-ideas-brainstorm.md",
                "content": """# Content Ideas Brainstorm

## Instagram Content Ideas
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

## TikTok/Reels Content Ideas
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

## YouTube Video Ideas
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

## Blog Post Topics
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

## Email Newsletter Ideas
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

## Trending Topics to Leverage
- _________________________________
- _________________________________
- _________________________________

## Evergreen Content Ideas
- _________________________________
- _________________________________
- _________________________________

## Collaboration Ideas
- _________________________________
- _________________________________
- _________________________________
"""
            }
        ]
    },
    {
        "title": "Wedding Planner Bundle",
        "niche": "Event Planning & Weddings",
        "sub_niche": "Wedding organization tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Wedding Budget Tracker",
                "description": "Comprehensive budget planner for weddings with vendor tracking and payment schedules.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_wedding-budget-tracker.md",
                "content": """# Wedding Budget Tracker

## Budget Overview
**Total Budget:** $__________
**Spent:** $__________
**Remaining:** $__________

## Venue & Catering (40%)
| Item | Est. Cost | Actual Cost | Paid | Balance |
|------|-----------|-------------|------|---------|
| Venue Rental | $_______ | $_______ | ☐ | $_______ |
| Catering | $_______ | $_______ | ☐ | $_______ |
| Bar Service | $_______ | $_______ | ☐ | $_______ |
| Cake | $_______ | $_______ | ☐ | $_______ |
| **Subtotal** | **$_______** | **$_______** | | **$_______** |

## Photography & Video (15%)
| Item | Est. Cost | Actual Cost | Paid | Balance |
|------|-----------|-------------|------|---------|
| Photographer | $_______ | $_______ | ☐ | $_______ |
| Videographer | $_______ | $_______ | ☐ | $_______ |
| **Subtotal** | **$_______** | **$_______** | | **$_______** |

## Attire (10%)
| Item | Est. Cost | Actual Cost | Paid | Balance |
|------|-----------|-------------|------|---------|
| Wedding Dress | $_______ | $_______ | ☐ | $_______ |
| Suit/Tux | $_______ | $_______ | ☐ | $_______ |
| Accessories | $_______ | $_______ | ☐ | $_______ |
| **Subtotal** | **$_______** | **$_______** | | **$_______** |
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Wedding Timeline Planner",
                "description": "12-month countdown timeline with monthly tasks and reminders.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_wedding-timeline-planner.md",
                "content": """# Wedding Timeline Planner

## 12 Months Before
- [ ] Set the date
- [ ] Create guest list
- [ ] Set budget
- [ ] Book venue
- [ ] Hire wedding planner (optional)

## 9 Months Before
- [ ] Book photographer
- [ ] Book videographer
- [ ] Select wedding party
- [ ] Start dress shopping

## 6 Months Before
- [ ] Order invitations
- [ ] Book florist
- [ ] Book DJ/band
- [ ] Plan honeymoon

## 3 Months Before
- [ ] Send invitations
- [ ] Final dress fitting
- [ ] Order wedding cake
- [ ] Confirm all vendors

## 1 Month Before
- [ ] Final headcount
- [ ] Confirm timeline with vendors
- [ ] Pick up rings
- [ ] Marriage license

## 1 Week Before
- [ ] Final vendor confirmations
- [ ] Pack for honeymoon
- [ ] Prepare payments/tips
- [ ] Rehearsal dinner
"""
            }
        ]
    },
    {
        "title": "Small Business Startup Kit",
        "niche": "Business & Entrepreneurship",
        "sub_niche": "Startup planning tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Business Plan Template",
                "description": "Complete business plan framework with financial projections.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_business-plan-template.md",
                "content": """# Business Plan Template

## Executive Summary
**Business Name:** _____________________
**Industry:** _____________________
**Mission Statement:**
_______________________________________________

## Business Description
**Products/Services:**
- _____________________
- _____________________
- _____________________

**Target Market:**
- _____________________
- _____________________

**Competitive Advantage:**
_______________________________________________

## Market Analysis
**Target Customers:**
- Demographics: _____________________
- Psychographics: _____________________
- Market Size: _____________________

**Competition:**
| Competitor | Strengths | Weaknesses |
|------------|-----------|------------|
| __________ | _________ | __________ |
| __________ | _________ | __________ |

## Financial Projections
**Year 1 Revenue:** $_____________
**Year 1 Expenses:** $_____________
**Break-even Point:** Month _______
"""
            }
        ]
    },
    {
        "title": "Meal Prep Planner Bundle",
        "niche": "Health & Nutrition",
        "sub_niche": "Meal planning tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Weekly Meal Prep Planner",
                "description": "Meal planning template with grocery list and nutrition tracking.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_weekly-meal-prep-planner.md",
                "content": """# Weekly Meal Prep Planner

## Week of: _______________

### Monday
| Meal | Menu | Calories | Prep Time |
|------|------|----------|-----------|
| Breakfast | ____________ | _____ | _____ |
| Lunch | ____________ | _____ | _____ |
| Dinner | ____________ | _____ | _____ |
| Snacks | ____________ | _____ | _____ |

### Tuesday
| Meal | Menu | Calories | Prep Time |
|------|------|----------|-----------|
| Breakfast | ____________ | _____ | _____ |
| Lunch | ____________ | _____ | _____ |
| Dinner | ____________ | _____ | _____ |
| Snacks | ____________ | _____ | _____ |

## Grocery List
**Proteins:**
- [ ] _________________
- [ ] _________________

**Vegetables:**
- [ ] _________________
- [ ] _________________

**Carbs:**
- [ ] _________________
- [ ] _________________

**Other:**
- [ ] _________________
- [ ] _________________

## Total Weekly Budget: $_______
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Nutrition Tracker",
                "description": "Daily nutrition and macros tracking sheet.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_nutrition-tracker.md",
                "content": """# Nutrition Tracker

## Daily Targets
- **Calories:** _______ kcal
- **Protein:** _______ g
- **Carbs:** _______ g
- **Fat:** _______ g
- **Water:** _______ oz

## Monday
| Meal | Food | Calories | Protein | Carbs | Fat |
|------|------|----------|---------|-------|-----|
| Breakfast | _____ | _____ | _____ | _____ | _____ |
| Lunch | _____ | _____ | _____ | _____ | _____ |
| Dinner | _____ | _____ | _____ | _____ | _____ |
| Snacks | _____ | _____ | _____ | _____ | _____ |
| **Total** | | **_____** | **_____** | **_____** | **_____** |

**Water Intake:** ☐☐☐☐☐☐☐☐ (8 glasses)
**Exercise:** _______________ (_____ min)
**Weight:** _______ lbs
"""
            }
        ]
    },
    {
        "title": "Student Study Planner Bundle",
        "niche": "Education & Learning",
        "sub_niche": "Academic planning tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Weekly Study Schedule",
                "description": "Time-blocked study planner with assignment tracking.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_weekly-study-schedule.md",
                "content": """# Weekly Study Schedule

## Week of: _______________

### Monday
| Time | Subject | Task | Priority | Done |
|------|---------|------|----------|------|
| __:__ - __:__ | _______ | __________ | H/M/L | ☐ |
| __:__ - __:__ | _______ | __________ | H/M/L | ☐ |
| __:__ - __:__ | _______ | __________ | H/M/L | ☐ |

### Tuesday
| Time | Subject | Task | Priority | Done |
|------|---------|------|----------|------|
| __:__ - __:__ | _______ | __________ | H/M/L | ☐ |
| __:__ - __:__ | _______ | __________ | H/M/L | ☐ |

## This Week's Deadlines
- [ ] _________________ (Due: ___/___)
- [ ] _________________ (Due: ___/___)
- [ ] _________________ (Due: ___/___)

## Study Goals
1. _____________________
2. _____________________
3. _____________________
"""
            }
        ]
    },
    {
        "title": "Home Cleaning Schedule Bundle",
        "niche": "Home & Organization",
        "sub_niche": "Cleaning routines",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Weekly Cleaning Checklist",
                "description": "Room-by-room cleaning schedule with daily, weekly, and monthly tasks.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_weekly-cleaning-checklist.md",
                "content": """# Weekly Cleaning Checklist

## Daily Tasks (All Rooms)
- [ ] Make beds
- [ ] Wipe counters
- [ ] Do dishes
- [ ] Quick floor sweep
- [ ] 10-minute tidy

## Kitchen (Monday)
- [ ] Clean countertops
- [ ] Wipe appliances
- [ ] Clean sink
- [ ] Mop floor
- [ ] Take out trash

## Bathrooms (Tuesday)
- [ ] Clean toilets
- [ ] Scrub showers/tubs
- [ ] Clean mirrors
- [ ] Wipe counters
- [ ] Mop floors

## Living Areas (Wednesday)
- [ ] Vacuum/sweep floors
- [ ] Dust surfaces
- [ ] Organize clutter
- [ ] Clean windows
- [ ] Fluff cushions

## Bedrooms (Thursday)
- [ ] Change sheets
- [ ] Dust furniture
- [ ] Vacuum floors
- [ ] Organize closets
- [ ] Clean mirrors

## Deep Clean (Friday)
- [ ] Baseboards
- [ ] Light fixtures
- [ ] Behind furniture
- [ ] Inside appliances
- [ ] Windows
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Monthly Deep Clean Schedule",
                "description": "Monthly deep cleaning tasks organized by room.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_monthly-deep-clean-schedule.md",
                "content": """# Monthly Deep Clean Schedule

## Month: _______________

### Week 1: Kitchen
- [ ] Clean oven
- [ ] Clean refrigerator
- [ ] Organize pantry
- [ ] Clean light fixtures
- [ ] Wash curtains

### Week 2: Bathrooms
- [ ] Clean grout
- [ ] Organize cabinets
- [ ] Wash bath mats
- [ ] Clean exhaust fans
- [ ] Descale fixtures

### Week 3: Living Areas
- [ ] Vacuum under furniture
- [ ] Clean upholstery
- [ ] Dust ceiling fans
- [ ] Clean electronics
- [ ] Organize shelves

### Week 4: Bedrooms
- [ ] Rotate mattresses
- [ ] Organize drawers
- [ ] Clean under beds
- [ ] Wash pillows
- [ ] Clean closets
"""
            }
        ]
    },
    {
        "title": "Fitness Workout Tracker Bundle",
        "niche": "Health & Fitness",
        "sub_niche": "Workout planning tools",
        "assets": [
            {
                "asset_id": "asset-001",
                "name": "Workout Log",
                "description": "Exercise tracking template with sets, reps, and progress notes.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-001_workout-log.md",
                "content": """# Workout Log

## Week of: _______________

### Monday - Upper Body
| Exercise | Set 1 | Set 2 | Set 3 | Set 4 | Notes |
|----------|-------|-------|-------|-------|-------|
| Bench Press | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Rows | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Shoulder Press | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Bicep Curls | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |

**Duration:** _______ min
**Energy Level:** 1 2 3 4 5

### Wednesday - Lower Body
| Exercise | Set 1 | Set 2 | Set 3 | Set 4 | Notes |
|----------|-------|-------|-------|-------|-------|
| Squats | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Deadlifts | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Lunges | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |
| Calf Raises | ___lbs x___ | ___lbs x___ | ___lbs x___ | ___lbs x___ | _______ |

**Duration:** _______ min
**Energy Level:** 1 2 3 4 5

## Weekly Progress
**Weight:** _______ lbs
**Body Fat %:** _______ %
**Measurements:**
- Chest: _______ in
- Waist: _______ in
- Arms: _______ in
- Legs: _______ in
"""
            },
            {
                "asset_id": "asset-002",
                "name": "Fitness Goal Tracker",
                "description": "90-day fitness goal setting and progress tracking template.",
                "format": "PDF",
                "filename": "CONVERTPDF_asset-002_fitness-goal-tracker.md",
                "content": """# 90-Day Fitness Goal Tracker

## Starting Stats (Day 1)
**Date:** ___/___/___
**Weight:** _______ lbs
**Body Fat %:** _______ %
**Goal Weight:** _______ lbs

## 90-Day Goals
1. _____________________________
2. _____________________________
3. _____________________________

## Month 1 Progress
**Week 1:** _______ lbs | Workouts: ___
**Week 2:** _______ lbs | Workouts: ___
**Week 3:** _______ lbs | Workouts: ___
**Week 4:** _______ lbs | Workouts: ___

## Month 2 Progress
**Week 5:** _______ lbs | Workouts: ___
**Week 6:** _______ lbs | Workouts: ___
**Week 7:** _______ lbs | Workouts: ___
**Week 8:** _______ lbs | Workouts: ___

## Month 3 Progress
**Week 9:** _______ lbs | Workouts: ___
**Week 10:** _______ lbs | Workouts: ___
**Week 11:** _______ lbs | Workouts: ___
**Week 12:** _______ lbs | Workouts: ___

## Final Results (Day 90)
**Date:** ___/___/___
**Weight:** _______ lbs
**Body Fat %:** _______ %
**Total Change:** _______ lbs
**Goals Achieved:** ___/3
"""
            }
        ]
    }
]


def generate_mock_bundles():
    """Generate mock bundles with realistic data"""

    print("=" * 60)
    print("GENERATING MOCK BUNDLES FOR PACKAGER TESTING")
    print("=" * 60)

    # Initialize database
    db_manager = DatabaseManager(settings.db_path)
    bundle_queries = BundleQueries(db_manager)
    idea_queries = IdeaQueries(db_manager)

    created_bundles = []

    for i, config in enumerate(MOCK_BUNDLES, 1):
        print(f"\n[{i}/{len(MOCK_BUNDLES)}] Creating: {config['title']}")

        # Generate IDs
        bundle_id = f"mock-bundle-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8]}"
        idea_id = f"mock-idea-{uuid4().hex[:8]}"

        # Create idea in database
        idea = Idea(
            idea_id=idea_id,
            research_session_id=f"mock-session-{uuid4().hex[:8]}",
            title=config["title"],
            niche=config["niche"],
            sub_niche=config["sub_niche"],
            priority="A",
            roi_estimate=4.5,
            idea_json=json.dumps({
                "title": config["title"],
                "niche": config["niche"],
                "sub_niche": config["sub_niche"]
            })
        )

        if not idea_queries.create(idea):
            print(f"  [FAIL] Failed to create idea in database")
            continue

        print(f"  [OK] Created idea: {idea_id}")

        # Create planner output
        planner_output = {
            "bundle_id": bundle_id,
            "title": config["title"],
            "niche": config["niche"],
            "sub_niche": config["sub_niche"],
            "description": f"A comprehensive {config['niche'].lower()} bundle with professional templates and tools.",
            "assets": [],
            "target_persona": {
                "name": "Motivated Individual",
                "age_range": "25-45",
                "pain_points": ["Needs organization", "Wants to improve productivity"]
            },
            "brand_voice": {
                "tone": "Professional and encouraging",
                "style": "Clean and modern"
            },
            "pricing": {
                "etsy": {"price": 12.99, "currency": "USD"},
                "gumroad": {"price": 14.99, "currency": "USD"}
            },
            "marketplace_metadata": {
                "tags": ["productivity", "planner", "template", "printable"],
                "categories": ["Templates", "Planners"]
            }
        }

        # Add assets to planner output
        for asset in config["assets"]:
            planner_output["assets"].append({
                "asset_id": asset["asset_id"],
                "name": asset["name"],
                "description": asset["description"],
                "format": asset["format"],
                "type": "template"
            })

        # Create bundle in database
        bundle = Bundle(
            bundle_id=bundle_id,
            idea_id=idea_id,
            current_step="maker",
            status="completed",
            planner_output=json.dumps(planner_output)
        )

        if not bundle_queries.create(bundle):
            print(f"  [FAIL] Failed to create bundle in database")
            continue

        print(f"  [OK] Created bundle: {bundle_id}")

        # Create bundle directory structure
        bundle_dir = settings.get_bundle_dir(bundle_id)
        maker_output_dir = bundle_dir / "maker_output"
        maker_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"  [OK] Created directory: {maker_output_dir}")

        # Create assets
        for asset in config["assets"]:
            # Create asset subdirectory
            asset_dir = maker_output_dir / f"{asset['asset_id']}-{asset['name'].lower().replace(' ', '-')}"
            asset_dir.mkdir(parents=True, exist_ok=True)

            # Write asset file
            asset_file = asset_dir / asset["filename"]
            asset_file.write_text(asset["content"], encoding="utf-8")

            # Write asset metadata
            metadata = {
                "asset_id": asset["asset_id"],
                "name": asset["name"],
                "description": asset["description"],
                "format": asset["format"],
                "file_size_mb": len(asset["content"]) / (1024 * 1024)
            }

            metadata_file = asset_dir / "asset_metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

            print(f"    [OK] Created asset: {asset['name']} ({asset['format']})")

        created_bundles.append({
            "bundle_id": bundle_id,
            "title": config["title"],
            "asset_count": len(config["assets"]),
            "path": str(bundle_dir)
        })

    print("\n" + "=" * 60)
    print("MOCK BUNDLE GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nCreated {len(created_bundles)} mock bundles:\n")

    for bundle in created_bundles:
        print(f"[BUNDLE] {bundle['title']}")
        print(f"   ID: {bundle['bundle_id']}")
        print(f"   Assets: {bundle['asset_count']}")
        print(f"   Path: {bundle['path']}")
        print()

    print("You can now test the packager with these bundles!")
    print("Use the UI to navigate to the 'Library > Ready to Generate' tab")
    print("and click 'Generate Assets' on any of these bundles.\n")

    return created_bundles


if __name__ == "__main__":
    try:
        bundles = generate_mock_bundles()
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
