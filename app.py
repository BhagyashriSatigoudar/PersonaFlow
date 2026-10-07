import pickle
import pandas as pd
from datetime import datetime
from google import genai


from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

# =====================================
# GEMINI AI
# =====================================

gemini_client = genai.Client()

app = Flask(__name__)
app.secret_key = "milestone1-secret-key"

import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "milestone1"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# =====================================
# LOAD FINANCIAL FORECASTING MODEL
# =====================================

with open("models/finance_model.pkl", "rb") as file:
    finance_model = pickle.load(file)


with open("models/category_encoder.pkl", "rb") as file:
    category_encoder = pickle.load(file)

# =====================================
# LOAD HABIT / PRODUCTIVITY MODEL
# =====================================

with open("models/habit_model.pkl", "rb") as file:
    habit_model = pickle.load(file)    

# =====================================
# LOAD STUDY PERFORMANCE MODEL
# =====================================

with open("models/study_model.pkl", "rb") as file:
    study_model = pickle.load(file)  

@app.route("/simulation")
def simulation():

    # =====================================
    # CHECK LOGIN
    # =====================================

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================
    # 1. GET ACTUAL FINANCIAL DATA
    # =====================================

    cursor.execute(
        """
        SELECT category, amount, frequency
        FROM financial_data
        WHERE user_id = %s
        """,
        (user_id,)
    )

    financial_rows = cursor.fetchall()

    total_income = 0
    total_expense = 0
    total_savings = 0

    # Convert different frequencies to monthly values
    def monthly_amount(amount, frequency):

        amount = float(amount)

        if frequency is None:
            return amount

        frequency = str(frequency).lower().strip()

        if frequency in ["daily", "day"]:
            return amount * 30

        elif frequency in ["weekly", "week"]:
            return amount * 4.33

        elif frequency in ["yearly", "annual", "year"]:
            return amount / 12

        # Monthly
        return amount

    for row in financial_rows:

        category = row[0]
        amount = row[1]
        frequency = row[2]

        if category is None:
            continue

        amount = monthly_amount(amount, frequency)

        category = category.lower().strip()

        if category == "income":
            total_income += amount

        elif category == "expense":
            total_expense += amount

        elif category == "savings":
            total_savings += amount

    # =====================================
    # 2. CURRENT FINANCIAL BASELINE
    # =====================================

    current_monthly_saving = (
        total_income - total_expense
    )

    current_monthly_saving = max(
        current_monthly_saving, 0
    )

    if total_income > 0:

        current_savings_rate = (
            current_monthly_saving
            / total_income
        ) * 100

    else:

        current_savings_rate = 0

    # =====================================
    # 3. FIVE YEAR FINANCIAL SIMULATION
    # =====================================

    years = 5
    months = years * 12

    # Expected = current actual trend
    expected_monthly_saving = current_monthly_saving

    # Best = 30% savings
    best_monthly_saving = total_income * 0.30

    # Risk = 10% savings
    risk_monthly_saving = total_income * 0.10

    expected_financial = round(
        expected_monthly_saving * months, 2
    )

    best_financial = round(
        best_monthly_saving * months, 2
    )

    risk_financial = round(
        risk_monthly_saving * months, 2
    )

    # =====================================
    # 4. FINANCIAL GRAPH DATA
    # =====================================

    current_graph = []
    best_financial_graph = []
    risk_financial_graph = []

    for year in range(1, 6):

        current_graph.append(
            round(
                expected_monthly_saving
                * 12
                * year,
                2
            )
        )

        best_financial_graph.append(
            round(
                best_monthly_saving
                * 12
                * year,
                2
            )
        )

        risk_financial_graph.append(
            round(
                risk_monthly_saving
                * 12
                * year,
                2
            )
        )

    # =====================================
    # 5. GET ACTUAL STUDY DATA
    # =====================================

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(study_hours), 0),
            COUNT(*),
            COALESCE(AVG(study_hours), 0)
        FROM study_data
        WHERE user_id = %s
        """,
        (user_id,)
    )

    study_result = cursor.fetchone()

    total_study_hours = float(
        study_result[0]
    )

    study_records = study_result[1]

    average_study_hours = float(
        study_result[2]
    )

    # =====================================
    # 6. STUDY SIMULATION
    # =====================================

    # Expected = actual average
    expected_study = average_study_hours

    # Best = 25% improvement
    best_study = average_study_hours * 1.25

    # Risk = 25% reduction
    risk_study = average_study_hours * 0.75

    study_expected_5year = round(
        expected_study * 365 * 5, 2
    )

    study_best_5year = round(
        best_study * 365 * 5, 2
    )

    study_risk_5year = round(
        risk_study * 365 * 5, 2
    )

    # =====================================
    # 7. STUDY GRAPH DATA
    # =====================================

    study_expected_graph = []
    study_best_graph = []
    study_risk_graph = []

    for year in range(1, 6):

        study_expected_graph.append(
            round(
                expected_study
                * 365
                * year,
                2
            )
        )

        study_best_graph.append(
            round(
                best_study
                * 365
                * year,
                2
            )
        )

        study_risk_graph.append(
            round(
                risk_study
                * 365
                * year,
                2
            )
        )

    # =====================================
    # 8. GET ACTUAL HABIT DATA
    # =====================================

    cursor.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(AVG(duration), 0)
        FROM habit_data
        WHERE user_id = %s
        """,
        (user_id,)
    )

    habit_result = cursor.fetchone()

    habit_records = habit_result[0]

    average_habit_duration = float(
        habit_result[1]
    )

    # Completed habits
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM habit_data
        WHERE user_id = %s
        AND LOWER(status) = 'completed'
        """,
        (user_id,)
    )

    completed_habits = cursor.fetchone()[0]

    # =====================================
    # 9. ACTUAL HABIT CONSISTENCY
    # =====================================

    if habit_records > 0:

        habit_consistency = (
            completed_habits
            / habit_records
        ) * 100

    else:

        habit_consistency = 0

    # =====================================
    # 10. FITNESS / PRODUCTIVITY SIMULATION
    # =====================================

    # Base score from actual habit consistency
    current_productivity = habit_consistency

    # Expected = current habit pattern
    expected_productivity = current_productivity

    # Best = improve consistency by 15 points
    best_productivity = min(
        current_productivity + 15,
        100
    )

    # Risk = decrease consistency by 15 points
    risk_productivity = max(
        current_productivity - 15,
        0
    )

    # =====================================
    # 11. PRODUCTIVITY GRAPH
    # =====================================

    productivity_expected_graph = []
    productivity_best_graph = []
    productivity_risk_graph = []

    for year in range(1, 6):

        expected_score = min(
            expected_productivity
            + (year - 1) * 1,
            100
        )

        best_score = min(
            best_productivity
            + (year - 1) * 2,
            100
        )

        risk_score = max(
            risk_productivity
            - (year - 1) * 1,
            0
        )

        productivity_expected_graph.append(
            round(expected_score, 2)
        )

        productivity_best_graph.append(
            round(best_score, 2)
        )

        productivity_risk_graph.append(
            round(risk_score, 2)
        )

    # =====================================
    # 12. MBA SCENARIO
    # =====================================

    # Uses actual income as baseline.
    # MBA scenario applies a project assumption
    # of 20% long-term income improvement.

    mba_income_growth = 0.20

    mba_graph = []

    for year in range(1, 6):

        current_income = (
            total_income * 12 * year
        )

        mba_income = (
            total_income
            * 12
            * year
            * (1 + mba_income_growth)
        )

        mba_graph.append(
            round(mba_income, 2)
        )

    # =====================================
    # 13. BUY VS RENT SCENARIO
    # =====================================

    # Uses actual monthly income and expenses.
    # These are simulation assumptions, not
    # guaranteed real-world property values.

    current_housing_cost = (
        total_expense * 0.30
    )

    rent_cost = (
        total_income * 0.20
    )

    buy_cost = (
        total_income * 0.25
    )

    buy_rent_graph = []

    for year in range(1, 6):

        rent_total = (
            rent_cost
            * 12
            * year
        )

        buy_total = (
            buy_cost
            * 12
            * year
        )

        buy_rent_graph.append({
            "year": year,
            "rent": round(
                rent_total, 2
            ),
            "buy": round(
                buy_total, 2
            )
        })

    # =====================================
    # 14. WELL-BEING BASELINE
    # =====================================

    financial_score = min(
        current_savings_rate,
        100
    )

    study_score = min(
        average_study_hours * 10,
        100
    )

    habit_score = habit_consistency

    wellbeing_score = round(
        (
            financial_score
            + study_score
            + habit_score
        ) / 3,
        2
    )

    # =====================================
    # 15. WELL-BEING SCENARIOS
    # =====================================

    wellbeing_expected = wellbeing_score

    wellbeing_best = min(
        wellbeing_score + 15,
        100
    )

    wellbeing_risk = max(
        wellbeing_score - 15,
        0
    )

    # =====================================
    # 16. WELL-BEING GRAPH
    # =====================================

    wellbeing_expected_graph = []
    wellbeing_best_graph = []
    wellbeing_risk_graph = []

    for year in range(1, 6):

        expected = min(
            wellbeing_expected
            + (year - 1) * 1,
            100
        )

        best = min(
            wellbeing_best
            + (year - 1) * 2,
            100
        )

        risk = max(
            wellbeing_risk
            - (year - 1) * 1,
            0
        )

        wellbeing_expected_graph.append(
            round(expected, 2)
        )

        wellbeing_best_graph.append(
            round(best, 2)
        )

        wellbeing_risk_graph.append(
            round(risk, 2)
        )

    # =====================================
    # 17. PERSONALIZED RECOMMENDATION
    # =====================================

    recommendations = []

    if total_income <= 0:

        recommendations.append(
            "Add financial income data to improve the simulation."
        )

    elif current_savings_rate < 20:

        recommendations.append(
            "Your historical financial data shows a low savings rate. "
            "Increasing savings gradually may improve the long-term projection."
        )

    else:

        recommendations.append(
            "Your historical financial data shows a positive savings pattern. "
            "Maintaining consistent savings can support the projected financial path."
        )

    if average_study_hours > 0:

        recommendations.append(
            f"Your historical study average is "
            f"{average_study_hours:.2f} hours per record. "
            "Improving consistency can increase the best-case study scenario."
        )

    else:

        recommendations.append(
            "Add study records to generate a personalized study simulation."
        )

    if habit_records > 0:

        recommendations.append(
            f"Your historical habit completion rate is "
            f"{habit_consistency:.2f}%. "
            "Improving habit consistency increases the simulated productivity outcome."
        )

    else:

        recommendations.append(
            "Add habit records to generate a personalized fitness simulation."
        )

    recommendation = " ".join(
        recommendations
    )

    # =====================================
    # 18. CLOSE DATABASE
    # =====================================

    cursor.close()
    conn.close()

    # =====================================
    # 19. SEND DATA TO SIMULATION.HTML
    # =====================================

    return render_template(
        "simulation.html",

        # Financial data
        total_income=round(
            total_income, 2
        ),

        total_expense=round(
            total_expense, 2
        ),

        total_savings=round(
            total_savings, 2
        ),

        current_savings_rate=round(
            current_savings_rate, 2
        ),

        current_path=expected_financial,

        save_25=round(
            total_income * 0.25 * months,
            2
        ),

        save_30=best_financial,

        # Financial Expected / Best / Risk
        expected_financial=expected_financial,
        best_financial=best_financial,
        risk_financial=risk_financial,

        current_graph=current_graph,

        save25_graph=[
            round(
                total_income * 0.25 * 12 * year,
                2
            )
            for year in range(1, 6)
        ],

        save30_graph=best_financial_graph,

        risk_financial_graph=risk_financial_graph,

        # Study data
        total_study_hours=round(
            total_study_hours, 2
        ),

        study_records=study_records,

        average_study_hours=round(
            average_study_hours, 2
        ),

        expected_study=round(
            expected_study, 2
        ),

        best_study=round(
            best_study, 2
        ),

        risk_study=round(
            risk_study, 2
        ),

        study_expected_graph=study_expected_graph,

        study_best_graph=study_best_graph,

        study_risk_graph=study_risk_graph,

        # Habit data
        habit_records=habit_records,

        completed_habits=completed_habits,

        average_habit_duration=round(
            average_habit_duration, 2
        ),

        habit_consistency=round(
            habit_consistency, 2
        ),

        expected_productivity=round(
            expected_productivity, 2
        ),

        best_productivity=round(
            best_productivity, 2
        ),

        risk_productivity=round(
            risk_productivity, 2
        ),

        productivity_expected_graph=
            productivity_expected_graph,

        productivity_best_graph=
            productivity_best_graph,

        productivity_risk_graph=
            productivity_risk_graph,

        # MBA
        mba_graph=mba_graph,

        # Buy vs Rent
        current_housing_cost=round(
            current_housing_cost, 2
        ),

        rent_cost=round(
            rent_cost, 2
        ),

        buy_cost=round(
            buy_cost, 2
        ),

        buy_rent_graph=buy_rent_graph,

        # Well-being
        wellbeing_score=round(
            wellbeing_score, 2
        ),

        wellbeing_expected=
            round(wellbeing_expected, 2),

        wellbeing_best=
            round(wellbeing_best, 2),

        wellbeing_risk=
            round(wellbeing_risk, 2),

        wellbeing_expected_graph=
            wellbeing_expected_graph,

        wellbeing_best_graph=
            wellbeing_best_graph,

        wellbeing_risk_graph=
            wellbeing_risk_graph,

        # Recommendation
        recommendation=recommendation,

        recommendation_level=(
            "High"
            if current_savings_rate < 20
            else "Medium"
            if current_savings_rate < 30
            else "Low"
        )
    )

@app.route("/")
def home():
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        age = request.form.get("age") or None
        occupation = request.form.get("occupation")
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (full_name, email, password_hash, age, occupation)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (full_name, email, password_hash, age, occupation)
            )

            conn.commit()

            cursor.close()
            conn.close()

            flash("Account created successfully!", "success")

            return redirect(url_for("register"))

        except psycopg2.IntegrityError:
            return "Email already registered."

        except Exception as e:
            return f"Registration error: {e}"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, full_name, password_hash
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user[2], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # RECORD COUNTS
    # =========================

    cursor.execute("""
        SELECT COUNT(*)
        FROM financial_data
        WHERE user_id = %s
    """, (user_id,))
    finance_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM study_data
        WHERE user_id = %s
    """, (user_id,))
    study_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM habit_data
        WHERE user_id = %s
    """, (user_id,))
    habit_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM activity_history
        WHERE user_id = %s
    """, (user_id,))
    activity_count = cursor.fetchone()[0]


    # =========================
    # FINANCIAL TOTALS
    # =========================

    cursor.execute("""
        SELECT

            COALESCE(
                SUM(
                    CASE
                        WHEN LOWER(category) = 'income'
                        THEN amount
                        ELSE 0
                    END
                ), 0
            ),

            COALESCE(
                SUM(
                    CASE
                        WHEN LOWER(category) = 'expense'
                        THEN amount
                        ELSE 0
                    END
                ), 0
            ),

            COALESCE(
                SUM(
                    CASE
                        WHEN LOWER(category) = 'savings'
                        THEN amount
                        ELSE 0
                    END
                ), 0
            )

        FROM financial_data

        WHERE user_id = %s

    """, (user_id,))

    total_income, total_expense, total_savings = cursor.fetchone()

    # IMPORTANT:
    # PostgreSQL returns Decimal values.
    # Convert them to float before using them
    # in calculations or sending them to HTML.

    total_income = float(total_income or 0)
    total_expense = float(total_expense or 0)
    total_savings = float(total_savings or 0)


    # =========================
    # FINANCIAL CHART
    # =========================

    finance_labels = [
        "Income",
        "Expense",
        "Savings"
    ]

    finance_values = [
        total_income,
        total_expense,
        total_savings
    ]


    # =========================
    # STUDY DATA
    # =========================

    cursor.execute("""
        SELECT
            TO_CHAR(study_date, 'DD Mon'),
            study_hours

        FROM study_data

        WHERE user_id = %s

        ORDER BY study_date DESC

        LIMIT 7

    """, (user_id,))

    study_rows = cursor.fetchall()

    study_rows.reverse()

    study_labels = [
        row[0]
        for row in study_rows
    ]

    study_values = [
        float(row[1] or 0)
        for row in study_rows
    ]

    if not study_labels:
        study_labels = ["No Data"]
        study_values = [0]


    # =========================
    # TOTAL STUDY HOURS
    # =========================

    cursor.execute("""
        SELECT
            COALESCE(SUM(study_hours), 0)

        FROM study_data

        WHERE user_id = %s

    """, (user_id,))

    study_hours = cursor.fetchone()[0]

    # Convert Decimal to float

    study_hours = float(study_hours or 0)


    # =========================
    # HABIT DATA
    # =========================

    cursor.execute("""
        SELECT
            COUNT(*),

            COALESCE(SUM(duration), 0),

            COUNT(*) FILTER (
                WHERE LOWER(status) = 'completed'
            )

        FROM habit_data

        WHERE user_id = %s

    """, (user_id,))

    habit_count, habit_minutes, completed_habits = cursor.fetchone()

    # Convert numeric PostgreSQL value

    habit_minutes = float(habit_minutes or 0)

    completed_habits = int(completed_habits or 0)


    # =========================
    # EXPENSE BREAKDOWN
    # =========================

    expense_labels = [
        "Income",
        "Expense",
        "Savings"
    ]

    expense_values = [
        total_income,
        total_expense,
        total_savings
    ]


    # =========================
    # FUTURE SIMULATION
    # =========================

    current_savings = total_savings

    expected_savings = current_savings * 1.10

    risk_savings = current_savings * 0.90


    # =========================
    # CLOSE DATABASE
    # =========================

    cursor.close()
    conn.close()


    # =========================
    # SEND DATA TO DASHBOARD
    # =========================

    return render_template(

        "dashboard.html",

        # Counts
        finance_count=finance_count,
        study_count=study_count,
        habit_count=habit_count,
        activity_count=activity_count,

        # Finance
        total_income=total_income,
        total_expense=total_expense,
        total_savings=total_savings,

        finance_labels=finance_labels,
        finance_values=finance_values,

        # Study
        study_hours=study_hours,
        study_labels=study_labels,
        study_values=study_values,

        # Habits
        habit_minutes=habit_minutes,
        completed_habits=completed_habits,

        # Expense chart
        expense_labels=expense_labels,
        expense_values=expense_values,

        # Simulation
        current_savings=current_savings,
        expected_savings=expected_savings,
        risk_savings=risk_savings
    )

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"]
        age = request.form.get("age") or None
        occupation = request.form.get("occupation")
        goals = request.form.get("goals")

        cursor.execute(
            """
            UPDATE users
            SET full_name = %s,
                age = %s,
                occupation = %s,
                goals = %s
            WHERE id = %s
            """,
            (full_name, age, occupation, goals, user_id)
        )

        conn.commit()

        session["user_name"] = full_name

        flash("Profile updated successfully!")

    cursor.execute(
        """
        SELECT id, full_name, email, age, occupation, goals
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("profile.html", user=user)


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# =====================================
# FINANCE ANALYSIS
# + AI EXPENSE PREDICTION
# + 7 DAY FINANCIAL FORECAST
# =====================================

@app.route("/finance", methods=["GET", "POST"])
def finance():

    # =====================================
    # CHECK LOGIN
    # =====================================

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    prediction = None

    # Future forecast data
    forecast_days = []
    forecast_amounts = []


    # =====================================
    # HANDLE FORM SUBMISSIONS
    # =====================================

    if request.method == "POST":

        action = request.form.get("action")


        # =====================================
        # SAVE FINANCIAL DATA
        # =====================================

        if action == "save":

            try:

                category = request.form["category"]

                amount = float(
                    request.form["amount"]
                )

                frequency = request.form["frequency"]

                description = request.form.get(
                    "description"
                )


                conn = get_db_connection()
                cursor = conn.cursor()


                cursor.execute(
                    """
                    INSERT INTO financial_data
                    (
                        user_id,
                        category,
                        amount,
                        frequency,
                        description
                    )

                    VALUES (%s, %s, %s, %s, %s)

                    RETURNING id
                    """,
                    (
                        user_id,
                        category,
                        amount,
                        frequency,
                        description
                    )
                )


                finance_id = cursor.fetchone()[0]


                # Save activity history

                cursor.execute(
                    """
                    INSERT INTO activity_history
                    (
                        user_id,
                        activity_type,
                        activity_id,
                        description
                    )

                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        "Finance",
                        finance_id,
                        f"{category} - ₹{amount}"
                    )
                )


                conn.commit()

                cursor.close()
                conn.close()


                flash(
                    "Financial data saved successfully!",
                    "success"
                )


                return redirect(
                    url_for("finance")
                )


            except Exception as e:

                flash(
                    f"Error saving financial data: {str(e)}",
                    "error"
                )


        # =====================================
        # AI EXPENSE PREDICTION
        # =====================================

        elif action == "predict":

            try:

                # =====================================
                # GET USER INPUT
                # =====================================

                income = float(
                    request.form["income"]
                )

                budget = float(
                    request.form["budget"]
                )

                transaction_count = int(
                    request.form["transaction_count"]
                )

                category = request.form[
                    "prediction_category"
                ]


                # =====================================
                # ENCODE CATEGORY
                # =====================================

                category_encoded = category_encoder.transform(
                    [category]
                )[0]


                # =====================================
                # CURRENT DATE
                # =====================================

                today = datetime.now()


                # =====================================
                # CREATE MODEL INPUT
                # =====================================

                prediction_data = pd.DataFrame(

                    [[
                        income,
                        budget,
                        transaction_count,
                        category_encoded,
                        today.year,
                        today.month,
                        today.day,
                        today.weekday()
                    ]],

                    columns=[
                        "Income",
                        "Budget",
                        "Transaction_Count",
                        "Category_Encoded",
                        "Year",
                        "Month",
                        "Day",
                        "DayOfWeek"
                    ]

                )


                # =====================================
                # CURRENT EXPENSE PREDICTION
                # =====================================

                predicted_expense = finance_model.predict(
                    prediction_data
                )[0]


                prediction = round(

                    max(
                        0,
                        float(predicted_expense)
                    ),

                    2
                )


                # =====================================
                # NEXT 7 DAYS FINANCIAL FORECAST
                # =====================================

                forecast_days = [
                    "Today",
                    "Day 1",
                    "Day 2",
                    "Day 3",
                    "Day 4",
                    "Day 5",
                    "Day 6",
                    "Day 7"
                ]


                # Today's predicted expense

                forecast_amounts = [
                    prediction
                ]


                # =====================================
                # PREDICT NEXT 7 DAYS
                # =====================================

                from datetime import timedelta


                for day in range(1, 8):

                    future_date = (
                        today +
                        timedelta(days=day)
                    )


                    # Gradually adjust transaction count
                    # to simulate future activity

                    future_transactions = (
                        transaction_count + day
                    )


                    # Create future model input

                    future_data = pd.DataFrame(

                        [[
                            income,
                            budget,
                            future_transactions,
                            category_encoded,
                            future_date.year,
                            future_date.month,
                            future_date.day,
                            future_date.weekday()
                        ]],

                        columns=[
                            "Income",
                            "Budget",
                            "Transaction_Count",
                            "Category_Encoded",
                            "Year",
                            "Month",
                            "Day",
                            "DayOfWeek"
                        ]

                    )


                    # Predict future expense

                    future_expense = finance_model.predict(
                        future_data
                    )[0]


                    future_expense = round(

                        max(
                            0,
                            float(future_expense)
                        ),

                        2
                    )


                    forecast_amounts.append(
                        future_expense
                    )


            except Exception as e:

                flash(
                    f"Prediction error: {str(e)}",
                    "error"
                )


    # =====================================
    # LOAD FINANCIAL DASHBOARD DATA
    # =====================================

    conn = get_db_connection()
    cursor = conn.cursor()


    # =====================================
    # TOTAL FINANCIAL RECORDS
    # =====================================

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM financial_data

        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_records = cursor.fetchone()[0]


    # =====================================
    # CATEGORY TOTALS
    # =====================================

    cursor.execute(
        """
        SELECT
            category,
            COALESCE(
                SUM(amount),
                0
            )

        FROM financial_data

        WHERE user_id = %s

        GROUP BY category

        ORDER BY category
        """,
        (user_id,)
    )


    category_data = cursor.fetchall()


    # Default values

    total_income = 0
    total_expense = 0
    total_savings = 0

    category_labels = []
    category_amounts = []


    # =====================================
    # PROCESS CATEGORY DATA
    # =====================================

    for row in category_data:

        category_name = row[0]

        amount = float(
            row[1]
        )


        category_labels.append(
            category_name
        )

        category_amounts.append(
            amount
        )


        # Calculate summary totals

        if category_name.lower() == "income":

            total_income += amount


        elif category_name.lower() == "expense":

            total_expense += amount


        elif category_name.lower() == "savings":

            total_savings += amount


    # =====================================
    # RECENT FINANCIAL ACTIVITIES
    # =====================================

    cursor.execute(
        """
        SELECT
            category,
            amount,
            frequency,
            description

        FROM financial_data

        WHERE user_id = %s

        ORDER BY id DESC

        LIMIT 5
        """,
        (user_id,)
    )


    recent_finances = cursor.fetchall()


    cursor.close()
    conn.close()


    # =====================================
    # SEND DATA TO FINANCE.HTML
    # =====================================

    return render_template(

        "finance.html",

        # Current AI Prediction

        prediction=prediction,


        # Financial Summary

        total_income=total_income,

        total_expense=total_expense,

        total_savings=total_savings,

        total_records=total_records,


        # Category Chart

        category_labels=category_labels,

        category_amounts=category_amounts,


        # Future Financial Forecast

        forecast_days=forecast_days,

        forecast_amounts=forecast_amounts,


        # Recent Activities

        recent_finances=recent_finances

    )
# =====================================
# STUDY TRACKING + ANALYTICS
# =====================================

@app.route("/study", methods=["GET", "POST"])
def study():

    # =====================================
    # CHECK LOGIN
    # =====================================

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]


    # =====================================
    # SAVE STUDY DATA
    # =====================================

    if request.method == "POST":

        try:

            subject = request.form["subject"]

            study_hours = float(
                request.form["study_hours"]
            )

            study_date = request.form["study_date"]

            study_method = request.form["study_method"]

            description = request.form.get(
                "description",
                ""
            )


            # DATABASE CONNECTION

            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "milestone1"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", "5432")
            )

            cursor = conn.cursor()


            # INSERT STUDY DATA

            cursor.execute(

                """
                INSERT INTO study_data
                (
                    user_id,
                    subject,
                    study_hours,
                    study_date,
                    study_method,
                    description
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,

                (
                    user_id,
                    subject,
                    study_hours,
                    study_date,
                    study_method,
                    description
                )

            )


            conn.commit()

            cursor.close()
            conn.close()


            flash(
                "Study data saved successfully!",
                "success"
            )


            return redirect(
                url_for("study")
            )


        except Exception as e:

            flash(
                f"Error saving study data: {str(e)}",
                "error"
            )


    # =====================================
    # DEFAULT VALUES
    # =====================================

    recent_studies = []

    subject_labels = []
    subject_hours = []

    method_labels = []
    method_hours = []

    # Historical trend

    trend_days = []
    trend_scores = []

    # Future trend

    future_trend_days = []
    future_trend_scores = []

    total_study_hours = 0

    total_records = 0

    most_studied_subject = "No data"

    average_daily_hours = 0


    try:

        # =====================================
        # DATABASE CONNECTION
        # =====================================

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "milestone1"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )



        cursor = conn.cursor()


        # =====================================
        # TOTAL STUDY HOURS
        # =====================================

        cursor.execute(

            """
            SELECT COALESCE(SUM(study_hours), 0)

            FROM study_data

            WHERE user_id = %s
            """,

            (user_id,)

        )


        total_study_hours = float(
            cursor.fetchone()[0]
        )


        # =====================================
        # TOTAL RECORDS
        # =====================================

        cursor.execute(

            """
            SELECT COUNT(*)

            FROM study_data

            WHERE user_id = %s
            """,

            (user_id,)

        )


        total_records = cursor.fetchone()[0]


        # =====================================
        # SUBJECT-WISE ANALYSIS
        # =====================================

        cursor.execute(

            """
            SELECT
                subject,
                SUM(study_hours) AS total_hours

            FROM study_data

            WHERE user_id = %s

            GROUP BY subject

            ORDER BY total_hours DESC
            """,

            (user_id,)

        )


        subject_data = cursor.fetchall()


        for row in subject_data:

            subject_labels.append(
                row[0]
            )

            subject_hours.append(
                float(row[1])
            )


        # =====================================
        # MOST STUDIED SUBJECT
        # =====================================

        if subject_data:

            most_studied_subject = (
                subject_data[0][0]
            )


        # =====================================
        # STUDY METHOD ANALYSIS
        # =====================================

        cursor.execute(

            """
            SELECT
                study_method,
                SUM(study_hours) AS total_hours

            FROM study_data

            WHERE user_id = %s

            GROUP BY study_method

            ORDER BY total_hours DESC
            """,

            (user_id,)

        )


        method_data = cursor.fetchall()


        for row in method_data:

            method_labels.append(
                row[0]
            )

            method_hours.append(
                float(row[1])
            )


        # =====================================
        # RECENT STUDY ACTIVITIES
        # =====================================

        cursor.execute(

            """
            SELECT
                subject,
                study_hours,
                study_date,
                study_method,
                description

            FROM study_data

            WHERE user_id = %s

            ORDER BY study_date DESC

            LIMIT 10
            """,

            (user_id,)

        )


        recent_studies = cursor.fetchall()


        # =====================================
        # LAST 7 DAYS HISTORICAL DATA
        # =====================================

        cursor.execute(

            """
            SELECT
                study_date,
                SUM(study_hours)

            FROM study_data

            WHERE
                user_id = %s

                AND study_date >=
                CURRENT_DATE - INTERVAL '6 days'

            GROUP BY study_date

            ORDER BY study_date ASC
            """,

            (user_id,)

        )


        weekly_data = cursor.fetchall()


        # =====================================
        # GET RECENT DATA FOR PREDICTION
        # LAST 7 DAYS
        # =====================================

        cursor.execute(

            """
            SELECT
                study_date,
                SUM(study_hours)

            FROM study_data

            WHERE
                user_id = %s

                AND study_date >=
                CURRENT_DATE - INTERVAL '6 days'

            GROUP BY study_date

            ORDER BY study_date ASC
            """,

            (user_id,)

        )


        prediction_data = cursor.fetchall()


        cursor.close()
        conn.close()


        # =====================================
        # IMPORT DATE TOOLS
        # =====================================

        from datetime import date, timedelta


        # =====================================
        # CREATE HISTORICAL 7-DAY TREND
        # =====================================

        daily_hours = {}


        for row in weekly_data:

            study_day = row[0]

            hours = float(row[1])

            daily_hours[
                study_day.strftime("%d %b")
            ] = hours


        for i in range(6, -1, -1):

            day = (
                date.today()
                - timedelta(days=i)
            )

            day_label = day.strftime(
                "%d %b"
            )


            trend_days.append(
                day_label
            )


            trend_scores.append(

                daily_hours.get(
                    day_label,
                    0
                )

            )


        # =====================================
        # CALCULATE AVERAGE DAILY STUDY HOURS
        # =====================================

        recent_hours = []


        for row in prediction_data:

            recent_hours.append(
                float(row[1])
            )


        if recent_hours:

            average_daily_hours = (
                sum(recent_hours)
                / len(recent_hours)
            )

        else:

            average_daily_hours = 0


        # =====================================
        # CALCULATE TREND DIRECTION
        # =====================================

        trend_change = 0


        if len(recent_hours) >= 2:

            first_half = recent_hours[
                :len(recent_hours) // 2
            ]

            second_half = recent_hours[
                len(recent_hours) // 2:
            ]


            if first_half and second_half:

                first_average = (
                    sum(first_half)
                    / len(first_half)
                )

                second_average = (
                    sum(second_half)
                    / len(second_half)
                )


                trend_change = (
                    second_average
                    - first_average
                )


        # =====================================
        # GENERATE NEXT 7 DAYS PREDICTION
        # =====================================

        for day_number in range(1, 8):

            future_date = (
                date.today()
                + timedelta(days=day_number)
            )


            future_trend_days.append(

                future_date.strftime(
                    "%d %b"
                )

            )


            # Gradual prediction based on
            # recent average and trend direction

            predicted_hours = (

                average_daily_hours

                + (
                    trend_change
                    * 0.20
                    * day_number
                )

            )


            # Study hours cannot be negative

            predicted_hours = max(
                0,
                predicted_hours
            )


            # Maximum reasonable daily limit

            predicted_hours = min(
                24,
                predicted_hours
            )


            future_trend_scores.append(

                round(
                    predicted_hours,
                    2
                )

            )


    except Exception as e:

        print(
            "Study analytics error:",
            str(e)
        )


    # =====================================
    # RETURN STUDY PAGE
    # =====================================

    return render_template(

        "study.html",

        # Summary

        total_study_hours=round(
            total_study_hours,
            2
        ),

        total_records=total_records,

        most_studied_subject=
            most_studied_subject,

        average_daily_hours=round(
            average_daily_hours,
            2
        ),


        # Subject Analytics

        subject_labels=
            subject_labels,

        subject_hours=
            subject_hours,


        # Method Analytics

        method_labels=
            method_labels,

        method_hours=
            method_hours,


        # Historical Trend

        trend_days=
            trend_days,

        trend_scores=
            trend_scores,


        # Future Prediction

        future_trend_days=
            future_trend_days,

        future_trend_scores=
            future_trend_scores,


        # Recent Activities

        recent_studies=
            recent_studies

    )
# =====================================
# HABIT & PRODUCTIVITY ANALYSIS
# =====================================

# =====================================
# HABIT & PRODUCTIVITY ANALYSIS
# =====================================

# =====================================
# HABIT & PRODUCTIVITY ANALYSIS
# + 7 DAY FUTURE PRODUCTIVITY TREND
# =====================================

@app.route("/habit", methods=["GET", "POST"])
def habit():

    # =====================================
    # CHECK LOGIN
    # =====================================

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]


    # =====================================
    # DEFAULT VALUES
    # =====================================

    prediction = None
    productivity_status = None

    future_productivity_days = []
    future_productivity_scores = []


    # =====================================
    # HANDLE POST REQUEST
    # =====================================

    if request.method == "POST":

        action = request.form.get("action")


        # =====================================
        # SAVE HABIT ACTIVITY
        # =====================================

        if action == "save":

            try:

                habit_name = request.form["habit_name"]

                duration = float(
                    request.form["duration"]
                )

                status = request.form["status"]

                habit_date = request.form["habit_date"]


                conn = get_db_connection()
                cursor = conn.cursor()


                # Save habit record
                cursor.execute(
                    """
                    INSERT INTO habit_data
                    (
                        user_id,
                        habit_name,
                        duration,
                        status,
                        habit_date
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        habit_name,
                        duration,
                        status,
                        habit_date
                    )
                )


                habit_id = cursor.fetchone()[0]


                # Save activity history
                cursor.execute(
                    """
                    INSERT INTO activity_history
                    (
                        user_id,
                        activity_type,
                        activity_id,
                        description
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        "Habit",
                        habit_id,
                        f"{habit_name} - {duration} minutes - {status}"
                    )
                )


                conn.commit()

                cursor.close()
                conn.close()


                flash(
                    "Habit activity saved successfully!",
                    "success"
                )


                return redirect(
                    url_for("habit")
                )


            except Exception as e:

                flash(
                    f"Error saving habit: {str(e)}",
                    "error"
                )


                try:

                    conn.rollback()
                    cursor.close()
                    conn.close()

                except:
                    pass


        # =====================================
        # AI PRODUCTIVITY PREDICTION
        # =====================================

        elif action == "predict":

            try:

                # Get values

                sleep_hours = float(
                    request.form["sleep_hours"]
                )

                exercise_minutes = float(
                    request.form["exercise_minutes"]
                )

                screen_time = float(
                    request.form["screen_time"]
                )

                tasks_completed = int(
                    request.form["tasks_completed"]
                )

                habit_duration = float(
                    request.form["habit_duration"]
                )

                habit_consistency = float(
                    request.form["habit_consistency"]
                )


                # =====================================
                # CURRENT PRODUCTIVITY PREDICTION
                # =====================================

                prediction_data = pd.DataFrame(

                    [[
                        sleep_hours,
                        exercise_minutes,
                        screen_time,
                        tasks_completed,
                        habit_duration,
                        habit_consistency
                    ]],

                    columns=[
                        "Sleep_Hours",
                        "Exercise_Minutes",
                        "Screen_Time",
                        "Tasks_Completed",
                        "Habit_Duration",
                        "Habit_Consistency"
                    ]

                )


                predicted_productivity = habit_model.predict(
                    prediction_data
                )[0]


                prediction = round(

                    max(
                        0,
                        min(
                            100,
                            float(predicted_productivity)
                        )
                    ),

                    2
                )


                # =====================================
                # PRODUCTIVITY STATUS
                # =====================================

                if prediction >= 80:

                    productivity_status = "Excellent 🚀"

                elif prediction >= 60:

                    productivity_status = "Good 👍"

                elif prediction >= 40:

                    productivity_status = "Average 🙂"

                else:

                    productivity_status = "Needs Improvement 📈"


                # =====================================
                # 7-DAY FUTURE PRODUCTIVITY TREND
                # =====================================

                future_productivity_days = [
                    "Today",
                    "Day 1",
                    "Day 2",
                    "Day 3",
                    "Day 4",
                    "Day 5",
                    "Day 6",
                    "Day 7"
                ]


                # Today's score
                future_productivity_scores = [
                    prediction
                ]


                # =====================================
                # CREATE FUTURE SCENARIOS
                # =====================================

                for day in range(1, 8):

                    # Small gradual improvements
                    # used for future scenario prediction

                    future_sleep = min(
                        8,
                        sleep_hours + (0.05 * day)
                    )

                    future_exercise = min(
                        120,
                        exercise_minutes + (2 * day)
                    )

                    future_screen = max(
                        0,
                        screen_time - (0.10 * day)
                    )

                    future_tasks = min(
                        20,
                        tasks_completed + day
                    )

                    future_duration = min(
                        180,
                        habit_duration + (2 * day)
                    )

                    future_consistency = min(
                        100,
                        habit_consistency + (1.5 * day)
                    )


                    # =====================================
                    # CREATE FUTURE MODEL INPUT
                    # =====================================

                    future_data = pd.DataFrame(

                        [[
                            future_sleep,
                            future_exercise,
                            future_screen,
                            future_tasks,
                            future_duration,
                            future_consistency
                        ]],

                        columns=[
                            "Sleep_Hours",
                            "Exercise_Minutes",
                            "Screen_Time",
                            "Tasks_Completed",
                            "Habit_Duration",
                            "Habit_Consistency"
                        ]

                    )


                    # =====================================
                    # RANDOM FOREST FUTURE PREDICTION
                    # =====================================

                    future_score = habit_model.predict(
                        future_data
                    )[0]


                    future_score = round(

                        max(
                            0,
                            min(
                                100,
                                float(future_score)
                            )
                        ),

                        2
                    )


                    future_productivity_scores.append(
                        future_score
                    )


            except Exception as e:

                flash(
                    f"Prediction error: {str(e)}",
                    "error"
                )


    # =====================================
    # LOAD HABIT DASHBOARD DATA
    # =====================================

    conn = get_db_connection()
    cursor = conn.cursor()


    # =====================================
    # TOTAL HABIT RECORDS
    # =====================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM habit_data
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_habits = cursor.fetchone()[0]


    # =====================================
    # HABIT STATUS COUNTS
    # =====================================

    cursor.execute(
        """
        SELECT
            status,
            COUNT(*)

        FROM habit_data

        WHERE user_id = %s

        GROUP BY status

        ORDER BY status
        """,
        (user_id,)
    )

    status_data = cursor.fetchall()


    status_labels = []
    status_counts = []

    completed_count = 0


    for row in status_data:

        status_name = row[0]
        count = row[1]

        status_labels.append(
            status_name
        )

        status_counts.append(
            count
        )

        if status_name.lower() == "completed":

            completed_count = count


    # =====================================
    # AVERAGE HABIT DURATION
    # =====================================

    cursor.execute(
        """
        SELECT
            COALESCE(
                AVG(duration),
                0
            )

        FROM habit_data

        WHERE user_id = %s
        """,
        (user_id,)
    )


    average_duration = float(
        cursor.fetchone()[0]
    )


    # =====================================
    # RECENT HABITS
    # =====================================

    cursor.execute(
        """
        SELECT
            habit_name,
            duration,
            status,
            habit_date

        FROM habit_data

        WHERE user_id = %s

        ORDER BY habit_date DESC

        LIMIT 10
        """,
        (user_id,)
    )


    recent_habits = cursor.fetchall()


    # =====================================
    # HABIT DURATION GRAPH DATA
    # =====================================

    habit_names = []
    habit_durations = []


    for habit_record in recent_habits:

        habit_names.append(
            habit_record[0]
        )

        habit_durations.append(
            float(
                habit_record[1]
            )
        )


    # =====================================
    # CLOSE DATABASE CONNECTION
    # =====================================

    cursor.close()
    conn.close()


    # =====================================
    # SEND DATA TO HABIT.HTML
    # =====================================

    return render_template(

        "habit.html",


        # AI Prediction

        prediction=prediction,

        productivity_status=
            productivity_status,


        # Summary Cards

        total_habits=
            total_habits,

        completed_count=
            completed_count,

        average_duration=round(
            average_duration,
            2
        ),


        # Habit Status Chart

        status_labels=
            status_labels,

        status_counts=
            status_counts,


        # Habit Duration Chart

        habit_names=
            habit_names,

        habit_durations=
            habit_durations,


        # Future Productivity Prediction

        future_productivity_days=
            future_productivity_days,

        future_productivity_scores=
            future_productivity_scores,


        # Recent Habit Table

        recent_habits=
            recent_habits

    )

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT activity_type, description, created_at
        FROM activity_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    activities = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        activities=activities
    )

# =====================================
# GENERATIVE AI CHATBOT
# =====================================

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():

    # =================================
    # CHECK LOGIN
    # =================================

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    user_message = None
    ai_response = None


    # =================================
    # HANDLE USER MESSAGE
    # =================================

    if request.method == "POST":

        user_message = request.form.get("message", "").strip()

        if not user_message:

            return render_template(
                "chatbot.html",
                message=None,
                user_message=None
            )


        try:

            # =================================
            # CONNECT TO DATABASE
            # =================================

            conn = get_db_connection()
            cursor = conn.cursor()


            # =================================
            # USER PROFILE
            # =================================

            cursor.execute(
                """
                SELECT
                    full_name,
                    age,
                    occupation,
                    goals
                FROM users
                WHERE id = %s
                """,
                (user_id,)
            )

            user = cursor.fetchone()


            # =================================
            # FINANCIAL DATA
            # =================================

            cursor.execute(
                """
                SELECT

                    COALESCE(
                        SUM(
                            CASE
                                WHEN LOWER(category) = 'income'
                                THEN amount
                                ELSE 0
                            END
                        ), 0
                    ),

                    COALESCE(
                        SUM(
                            CASE
                                WHEN LOWER(category) = 'expense'
                                THEN amount
                                ELSE 0
                            END
                        ), 0
                    ),

                    COALESCE(
                        SUM(
                            CASE
                                WHEN LOWER(category) = 'savings'
                                THEN amount
                                ELSE 0
                            END
                        ), 0
                    ),

                    COUNT(*)

                FROM financial_data

                WHERE user_id = %s
                """,
                (user_id,)
            )

            finance = cursor.fetchone()


            # =================================
            # STUDY DATA
            # =================================

            cursor.execute(
                """
                SELECT

                    COALESCE(SUM(study_hours), 0),

                    COALESCE(AVG(study_hours), 0),

                    COUNT(*)

                FROM study_data

                WHERE user_id = %s
                """,
                (user_id,)
            )

            study = cursor.fetchone()


            # =================================
            # HABIT DATA
            # =================================

            cursor.execute(
                """
                SELECT

                    COALESCE(SUM(duration), 0),

                    COUNT(*),

                    COALESCE(
                        SUM(
                            CASE
                                WHEN LOWER(status) = 'completed'
                                THEN 1
                                ELSE 0
                            END
                        ), 0
                    )

                FROM habit_data

                WHERE user_id = %s
                """,
                (user_id,)
            )

            habit = cursor.fetchone()


            # =================================
            # CLOSE DATABASE
            # =================================

            cursor.close()
            conn.close()


            # =================================
            # PREPARE USER PROFILE
            # =================================

            if user:

                full_name = user[0] or "User"
                age = user[1] or "Not provided"
                occupation = user[2] or "Not provided"
                goals = user[3] or "Not provided"

            else:

                full_name = "User"
                age = "Not provided"
                occupation = "Not provided"
                goals = "Not provided"


            # =================================
            # PREPARE FINANCIAL VALUES
            # =================================

            total_income = float(finance[0] or 0)

            total_expense = float(finance[1] or 0)

            total_savings = float(finance[2] or 0)

            finance_records = int(finance[3] or 0)


            # =================================
            # PREPARE STUDY VALUES
            # =================================

            total_study_hours = float(study[0] or 0)

            average_study_hours = float(study[1] or 0)

            study_records = int(study[2] or 0)


            # =================================
            # PREPARE HABIT VALUES
            # =================================

            total_habit_duration = float(habit[0] or 0)

            habit_records = int(habit[1] or 0)

            completed_habits = int(habit[2] or 0)


            # =================================
            # CALCULATE SAVING RATE
            # =================================

            if total_income > 0:

                saving_rate = (
                    (total_income - total_expense)
                    / total_income
                ) * 100

            else:

                saving_rate = 0


            # =================================
            # USER CONTEXT
            # =================================

            user_context = f"""

You are PersonaFlow AI Assistant.

You are a personal assistant for finance,
study, habits, productivity and future decisions.

Use the user's actual PersonaFlow data when
answering questions about the user.


=========================
USER PROFILE
=========================

Name: {full_name}

Age: {age}

Occupation: {occupation}

Goals: {goals}


=========================
FINANCIAL DATA
=========================

Total Income: ₹{total_income:.2f}

Total Expenses: ₹{total_expense:.2f}

Current Recorded Savings: ₹{total_savings:.2f}

Saving Rate: {saving_rate:.2f}%

Financial Records: {finance_records}


=========================
STUDY DATA
=========================

Total Study Hours: {total_study_hours:.2f}

Average Study Hours per Record: {average_study_hours:.2f}

Study Records: {study_records}


=========================
HABIT DATA
=========================

Total Habit Duration: {total_habit_duration:.2f} minutes

Habit Records: {habit_records}

Completed Habits: {completed_habits}


=========================
IMPORTANT RULES
=========================

1. Answer the user's exact question first.

2. Use the user's actual PersonaFlow data whenever
   the question is about their finances, study,
   habits or productivity.

3. NEVER give vague financial advice when an
   exact calculation can be performed.

4. If the user mentions a purchase price, identify
   the purchase price clearly.

5. For a purchase calculate:

   Amount Still Needed =
   Purchase Price - Current Recorded Savings

6. If the result is negative, use ₹0 as the
   Amount Still Needed.

7. For a purchase question ALWAYS show:

   Purchase Price
   Current Savings
   Amount Still Needed

8. If the user asks how much they should save
   every month, calculate:

   Monthly Saving =
   Amount Still Needed / Number of Months

9. If the user gives a number of months, use
   exactly that number.

10. If the user does not give a timeline, do not
    pretend there is an exact timeline.

    Instead, suggest a reasonable example timeline
    and clearly say it is an assumption.

11. If current savings are already greater than
    or equal to the purchase price, clearly tell
    the user that they already have enough recorded
    savings to cover the purchase.

12. If current savings are greater than the purchase
    price, also calculate:

    Remaining Savings =
    Current Savings - Purchase Price

13. Remind the user not to use all their savings
    and to maintain an emergency reserve.

14. ALWAYS show the arithmetic when making a
    financial calculation.

15. Use Indian Rupee ₹.

16. Keep answers short, clear and practical.

17. Do not invent personal data or financial values.

18. Do not expose database details, passwords,
    API keys or internal code.

19. Predictions and recommendations are estimates,
    not guarantees.


=========================
PURCHASE EXAMPLE
=========================

If the user asks:

"I want to buy a phone costing ₹60000.
How much do I need to save?"

And the user's current savings are ₹70000:

Purchase Price = ₹60,000

Current Savings = ₹70,000

Amount Still Needed:

₹60,000 - ₹70,000 = -₹10,000

Since the amount cannot be negative:

Amount Still Needed = ₹0

Remaining Savings:

₹70,000 - ₹60,000 = ₹10,000

Therefore say:

Purchase Price: ₹60,000
Current Savings: ₹70,000
Amount Still Needed: ₹0
Remaining Savings: ₹10,000

Based on the recorded savings, the user can
technically afford the purchase, but should
keep an emergency reserve.


=========================
MONTHLY SAVING EXAMPLE
=========================

If:

Purchase Price = ₹60,000
Current Savings = ₹20,000

Then:

Amount Still Needed:

₹60,000 - ₹20,000 = ₹40,000

If the user wants to buy it in 4 months:

Monthly Saving:

₹40,000 / 4 = ₹10,000 per month.


=========================
FINAL INSTRUCTION
=========================

Answer the user's question using the data above.

If a calculation is required:

1. Identify the numbers.
2. Perform the calculation.
3. Show the calculation.
4. Give the exact result.
5. Give a short practical recommendation.

"""


            # =================================
            # SEND TO GEMINI
            # =================================

            prompt = f"""

{user_context}


=========================
USER QUESTION
=========================

{user_message}


Answer the user's question now.

Remember:
If the question involves money or a purchase,
perform the exact calculation before giving
general advice.

Do not avoid the calculation.
"""


            response = gemini_client.models.generate_content(

                model="gemini-3.5-flash-lite",

                contents=prompt

            )


            ai_response = response.text


        except Exception as e:

            print("Gemini chatbot error:", str(e))

            ai_response = (
                "Sorry, I couldn't process your request "
                "right now. Please try again."
            )


    # =================================
    # DISPLAY CHATBOT PAGE
    # =================================

    return render_template(

        "chatbot.html",

        message=ai_response,

        user_message=user_message

    )
if __name__ == "__main__":
    app.run(debug=True)