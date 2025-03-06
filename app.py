import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Initialize Session State
if "all_expenses" not in st.session_state:
    st.session_state.all_expenses = pd.DataFrame(columns=["id", "year", "month", "category", "forecast", "actual", "comments"])
if "all_income" not in st.session_state:
    st.session_state.all_income = pd.DataFrame(columns=["year", "month", "income", "extra_income"])
if "next_id" not in st.session_state:
    st.session_state.next_id = 1
if "current_data" not in st.session_state:
    st.session_state.current_data = pd.DataFrame(columns=["id", "year", "month", "category", "forecast", "actual", "comments"])
if "selected_year" not in st.session_state:
    st.session_state.selected_year = datetime.now().year
if "selected_month" not in st.session_state:
    st.session_state.selected_month = datetime.now().month
if "income" not in st.session_state:
    st.session_state.income = 0.0
if "extra_income" not in st.session_state:
    st.session_state.extra_income = 0.0

# Helper Functions
def load_income(year, month):
    """Load income from session state for the selected year and month."""
    if not st.session_state.all_income.empty:
        row = st.session_state.all_income[(st.session_state.all_income["year"] == year) & (st.session_state.all_income["month"] == month)]
        if not row.empty:
            return float(row["income"].iloc[0]) or 0.0, float(row["extra_income"].iloc[0]) or 0.0
    return 0.0, 0.0

def save_income(year, month, income, extra_income):
    """Save or update income in session state."""
    mask = (st.session_state.all_income["year"] == year) & (st.session_state.all_income["month"] == month)
    if mask.any():
        st.session_state.all_income.loc[mask, "income"] = income
        st.session_state.all_income.loc[mask, "extra_income"] = extra_income
    else:
        new_row = pd.DataFrame({"year": [year], "month": [month], "income": [income], "extra_income": [extra_income]})
        st.session_state.all_income = pd.concat([st.session_state.all_income, new_row], ignore_index=True)

# Budget Analysis Functions
def suggest_budget_adjustments(expenses):
    suggestions = []
    for _, exp in expenses.iterrows():
        if exp["actual"] > exp["forecast"] * 1.2:
            suggestions.append(f"⚠️ Overspending in {exp['category']}! Consider reducing your budget.")
        elif exp["actual"] < exp["forecast"] * 0.8:
            suggestions.append(f"✅ Under budget in {exp['category']}! You might reallocate funds to savings.")
    return suggestions

def detect_unusual_spending(expenses, new_expense):
    category = new_expense["category"]
    past_spending = expenses[expenses["category"].str.lower() == category.lower()]["actual"].tolist()
    if not past_spending:
        return None
    avg_spending = sum(past_spending) / len(past_spending)
    if new_expense["actual"] > avg_spending * 1.5:
        return f"⚠️ Unusually high spending in {category} detected!"
    return None

def calculate_budget_score(expenses, total_income):
    total_actual = expenses["actual"].sum()
    total_forecast = expenses["forecast"].sum()
    overspent = total_actual > total_forecast
    savings_ratio = (total_income - total_actual) / total_income if total_income > 0 else 0
    score = 100
    if overspent:
        score -= 20
    if savings_ratio < 0.1:
        score -= 30
    elif savings_ratio > 0.2:
        score += 10
    return max(0, min(score, 100))

def analyze_budget(expenses, total_income, new_expense=None):
    insights = suggest_budget_adjustments(expenses)
    if new_expense:
        anomaly = detect_unusual_spending(expenses, new_expense)
        if anomaly:
            insights.append(anomaly)
    score = calculate_budget_score(expenses, total_income)
    insights.append(f"📊 Financial Health Score: {score}/100")
    return insights

# Sidebar for Filters
with st.sidebar:
    st.header("Filters")
    year = st.number_input("Year", min_value=2000, max_value=2100, value=st.session_state.selected_year)
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    month = st.selectbox("Month", month_names, index=st.session_state.selected_month - 1)
    month_num = month_names.index(month) + 1
    if st.button("Load Data"):
        st.session_state.selected_year = year
        st.session_state.selected_month = month_num
        st.session_state.current_data = st.session_state.all_expenses[
            (st.session_state.all_expenses["year"] == year) & 
            (st.session_state.all_expenses["month"] == month_num)
        ].copy()
        st.session_state.income, st.session_state.extra_income = load_income(year, month_num)

# Main App
st.title("BudgetByte")

# Income Management (Top Section)
st.subheader("Income Management")
with st.form("income_form"):
    income = st.number_input("Monthly Income ($)", min_value=0.0, value=st.session_state.income)
    extra_income = st.number_input("Extra Income ($)", min_value=0.0, value=st.session_state.extra_income)
    if st.form_submit_button("Update Income"):
        if income < 0 or extra_income < 0:
            st.error("Income values cannot be negative.")
        else:
            save_income(st.session_state.selected_year, st.session_state.selected_month, income, extra_income)
            st.session_state.income = income
            st.session_state.extra_income = extra_income
            st.success("Income updated!")

# Expense Management Section
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Expense Management")
    # Always show add expense fields
    st.write("### Add New Expense")
    category = st.text_input("Category", "")
    forecast = st.number_input("Forecast ($)", min_value=0.0, value=0.0)
    actual = st.number_input("Actual ($)", min_value=0.0, value=0.0)
    comments = st.text_input("Comments", "")
    if st.button("Add Expense"):
        if not category or forecast < 0 or actual < 0:
            st.error("Category, Forecast, and Actual must be filled, and values cannot be negative.")
        else:
            if not st.session_state.current_data.empty and any(exp["category"].lower() == category.lower() for _, exp in st.session_state.current_data.iterrows()):
                st.warning("Category already exists. Proceeding to add.")
            new_exp = pd.DataFrame({
                "id": [st.session_state.next_id],
                "year": [st.session_state.selected_year],
                "month": [st.session_state.selected_month],
                "category": [category],
                "forecast": [forecast],
                "actual": [actual],
                "comments": [comments]
            })
            st.session_state.all_expenses = pd.concat([st.session_state.all_expenses, new_exp], ignore_index=True)
            if st.session_state.current_data.empty or st.session_state.selected_year == year and st.session_state.selected_month == month_num:
                st.session_state.current_data = pd.concat([st.session_state.current_data, new_exp], ignore_index=True)
            st.session_state.next_id += 1
            st.success("Expense added!")

    # Show edit/delete options if data is loaded
    if not st.session_state.current_data.empty:
        st.write("### Edit or Delete Expense")
        selected_id = st.selectbox(
            "Select Expense",
            options=st.session_state.current_data["id"].tolist(),
            format_func=lambda x: st.session_state.current_data[st.session_state.current_data["id"] == x]["category"].iloc[0]
        )
        exp = st.session_state.current_data[st.session_state.current_data["id"] == selected_id].iloc[0]
        new_category = st.text_input("Category", value=exp["category"])
        new_forecast = st.number_input("Forecast ($)", min_value=0.0, value=float(exp["forecast"]))
        new_actual = st.number_input("Actual ($)", min_value=0.0, value=float(exp["actual"]))
        new_comments = st.text_input("Comments", value=exp["comments"])
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Save Changes"):
                if not new_category or new_forecast < 0 or new_actual < 0:
                    st.error("Category cannot be empty, and values cannot be negative.")
                else:
                    mask = st.session_state.all_expenses["id"] == selected_id
                    st.session_state.all_expenses.loc[mask, ["category", "forecast", "actual", "comments"]] = [new_category, new_forecast, new_actual, new_comments]
                    st.session_state.current_data.loc[st.session_state.current_data["id"] == selected_id, ["category", "forecast", "actual", "comments"]] = [new_category, new_forecast, new_actual, new_comments]
                    st.success("Expense updated!")
        with col_delete:
            if st.button("Delete Expense"):
                st.session_state.all_expenses = st.session_state.all_expenses[st.session_state.all_expenses["id"] != selected_id]
                st.session_state.current_data = st.session_state.current_data[st.session_state.current_data["id"] != selected_id]
                st.success("Expense deleted!")

with col2:
    st.subheader("Current Expenses")
    if not st.session_state.current_data.empty:
        styled_df = st.session_state.current_data[["category", "forecast", "actual", "comments"]].style.apply(
            lambda x: ['color: red' if x["actual"] > x["forecast"] else 'color: teal' for _ in x], axis=1
        ).format({"forecast": "${:.2f}", "actual": "${:.2f}"})
        st.dataframe(styled_df)
    else:
        st.info("No expenses loaded.")

# Summary Section
st.subheader("Summary")
if not st.session_state.current_data.empty:
    total_forecast = st.session_state.current_data["forecast"].sum()
    total_actual = st.session_state.current_data["actual"].sum()
    total_income = st.session_state.income + st.session_state.extra_income
    st.write(f"Total Forecast: ${total_forecast:,.2f}")
    st.write(f"Total Actual: ${total_actual:,.2f}")
    st.write(f"Budget Status: {'Surplus: $' + str(total_income - total_actual) if total_income >= total_actual else 'Deficit: $' + str(total_actual - total_income)}")

# Additional Features
if st.button("Calculate Net Actual"):
    if not st.session_state.current_data.empty:
        total_income = st.session_state.income + st.session_state.extra_income
        total_actual = st.session_state.current_data["actual"].sum()
        difference = total_income - total_actual
        st.write(f"Net Actual: ${difference:,.2f}")
        if total_actual > total_income:
            st.error("Your total income is not enough. Cut costs.")
        insights = analyze_budget(st.session_state.current_data, total_income)
        st.info("\n".join(insights))

if st.button("Show Expense Breakdown"):
    if not st.session_state.current_data.empty:
        fig = px.bar(st.session_state.current_data, x="category", y="actual", title="Expense Breakdown")
        st.plotly_chart(fig)
    else:
        st.warning("No expenses to display.")

if st.button("Use Previous Month Template"):
    prev_month, prev_year = (12, st.session_state.selected_year - 1) if st.session_state.selected_month == 1 else (st.session_state.selected_month - 1, st.session_state.selected_year)
    template_expenses = st.session_state.all_expenses[
        (st.session_state.all_expenses["year"] == prev_year) & 
        (st.session_state.all_expenses["month"] == prev_month)
    ].copy()
    if not template_expenses.empty:
        for _, exp in template_expenses.iterrows():
            new_exp = exp.copy()
            new_exp["id"] = st.session_state.next_id
            new_exp["year"] = st.session_state.selected_year
            new_exp["month"] = st.session_state.selected_month
            st.session_state.all_expenses = pd.concat([st.session_state.all_expenses, pd.DataFrame([new_exp])], ignore_index=True)
            st.session_state.current_data = pd.concat([st.session_state.current_data, pd.DataFrame([new_exp])], ignore_index=True)
            st.session_state.next_id += 1
        st.success(f"Copied {len(template_expenses)} expenses from previous month.")
    else:
        st.warning("No expenses found for previous month.")

# Data Export
st.subheader("Save Your Data")
if not st.session_state.all_expenses.empty:
    csv_expenses = st.session_state.all_expenses.to_csv(index=False)
    st.download_button("Download Expenses CSV", data=csv_expenses, file_name="expenses.csv", mime="text/csv")
if not st.session_state.all_income.empty:
    csv_income = st.session_state.all_income.to_csv(index=False)
    st.download_button("Download Income CSV", data=csv_income, file_name="income.csv", mime="text/csv")