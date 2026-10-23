import streamlit as st
import sqlite3
import re
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="SQL Interview Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Theme --------------------
st.markdown(r"""<style>
:root {
  --brand: #6d5dfc;
  --brand-dark: #5145cd;
  --ink: #172033;
  --muted: #697386;
  --line: rgba(120, 130, 155, .22);
  --surface: #ffffff;
}
.block-container {
  max-width: 1440px;
  padding-top: 1.35rem;
  padding-bottom: 3rem;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(109,93,252,.075), transparent 35%),
    var(--background-color);
}
[data-testid="stSidebar"] {
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 1.4rem;
}
.hero {
  position: relative;
  overflow: hidden;
  padding: 2rem 2.15rem;
  border-radius: 24px;
  margin: .25rem 0 1.5rem;
  background: linear-gradient(115deg, #211b4b 0%, #37317c 48%, #6257d9 100%);
  color: #fff;
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 18px 42px rgba(55,49,124,.17);
}
.hero:after {
  content: "";
  position: absolute;
  width: 270px; height: 270px;
  right: -70px; top: -125px;
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 50%;
  box-shadow: 0 0 0 28px rgba(255,255,255,.035),
              0 0 0 58px rgba(255,255,255,.025);
}
.hero h1 {
  margin: 0 0 .55rem 0;
  font-size: clamp(1.8rem, 3vw, 2.65rem);
  letter-spacing: -.045em;
  line-height: 1.15;
  color: #fff;
}
.hero p {
  margin: 0;
  color: rgba(255,255,255,.82);
  font-size: 1.03rem;
  max-width: 680px;
}
.eyebrow {
  display: inline-block;
  text-transform: uppercase;
  letter-spacing: .13em;
  font-size: .72rem;
  font-weight: 750;
  color: #c8c3ff;
  margin-bottom: .8rem;
}
.kpi {
  border: 1px solid var(--line);
  border-radius: 17px;
  padding: 1.1rem 1.2rem;
  min-height: 108px;
  background: var(--secondary-background-color);
  box-shadow: 0 4px 15px rgba(20,25,50,.025);
  transition: transform .18s ease, box-shadow .18s ease;
}
.kpi:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(20,25,50,.07);
}
.kpi .label {
  font-size: .76rem;
  font-weight: 750;
  letter-spacing: .075em;
  color: var(--muted);
}
.kpi .value {
  font-size: 1.85rem;
  line-height: 1.25;
  font-weight: 800;
  letter-spacing: -.04em;
  margin-top: .4rem;
  color: var(--text-color);
}
.tag {
  display: inline-block;
  padding: .22rem .62rem;
  border-radius: 999px;
  font-size: .72rem;
  font-weight: 650;
  background: rgba(109,93,252,.11);
  border: 1px solid rgba(109,93,252,.2);
  color: var(--text-color);
  vertical-align: middle;
}
.section-kicker {
  color: var(--muted);
  font-size: .83rem;
  margin-top: -.55rem;
}
div.stButton > button, div.stDownloadButton > button {
  border-radius: 11px;
  min-height: 2.65rem;
  font-weight: 650;
  transition: all .16s ease;
}
div.stButton > button[kind="primary"] {
  background: var(--brand);
  border-color: var(--brand);
}
div.stButton > button[kind="primary"]:hover {
  background: var(--brand-dark);
  border-color: var(--brand-dark);
  transform: translateY(-1px);
}
div[data-testid="stTextArea"] textarea {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: .91rem;
  line-height: 1.6;
  border-radius: 13px;
}
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] > div > div {
  border-radius: 11px;
}
div[data-testid="stTabs"] button {
  font-weight: 650;
}
div[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}
div[data-testid="stAlert"] {
  border-radius: 12px;
}
hr {
  border-color: var(--line);
}
@media (max-width: 760px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  .hero { padding: 1.5rem; border-radius: 18px; }
  .hero:after { opacity: .45; right: -160px; }
}
</style>""", unsafe_allow_html=True)

# -------------------- Sample database --------------------
CUSTOMERS = [
    (1, "Aarav", "Sharma", "Delhi", "2024-01-12"),
    (2, "Meera", "Kapoor", "Mumbai", "2024-02-03"),
    (3, "Ishaan", "Verma", "Pune", "2024-02-20"),
    (4, "Sara", "Khan", "Delhi", "2024-03-14"),
    (5, "Rohan", "Das", "Bengaluru", "2024-04-01"),
    (6, "Anaya", "Singh", "Mumbai", "2024-04-18"),
]
ORDERS = [
    (101, 1, "2024-05-01", 1200.0, "Delivered"),
    (102, 2, "2024-05-03", 850.0, "Delivered"),
    (103, 1, "2024-05-10", 400.0, "Cancelled"),
    (104, 3, "2024-05-11", 2400.0, "Delivered"),
    (105, 4, "2024-05-13", 1600.0, "Delivered"),
    (106, 2, "2024-05-18", 500.0, "Returned"),
    (107, 5, "2024-05-20", 3100.0, "Delivered"),
    (108, 6, "2024-05-22", 950.0, "Delivered"),
    (109, 3, "2024-06-02", 700.0, "Delivered"),
    (110, 4, "2024-06-04", 1100.0, "Delivered"),
    (111, 1, "2024-06-09", 1800.0, "Delivered"),
    (112, 5, "2024-06-12", 650.0, "Cancelled"),
]
EMPLOYEES = [
    (1, "Nisha", "Sales", 52000, "2022-03-15", None),
    (2, "Kabir", "Analytics", 68000, "2021-07-01", 1),
    (3, "Tara", "Sales", 61000, "2023-01-10", 1),
    (4, "Dev", "HR", 48000, "2020-11-22", None),
    (5, "Zoya", "Analytics", 74000, "2019-05-06", 2),
    (6, "Arjun", "IT", 72000, "2022-08-18", 2),
    (7, "Maya", "Sales", 59000, "2024-02-01", 3),
]

def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
        city TEXT, signup_date TEXT
    )""")
    cur.execute("""CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT,
        amount REAL, status TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )""")
    cur.execute("""CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY, employee_name TEXT, department TEXT,
        salary INTEGER, hire_date TEXT, manager_id INTEGER
    )""")
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", CUSTOMERS)
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", ORDERS)
    cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", EMPLOYEES)
    conn.commit()
    return conn

# -------------------- Question bank --------------------
QUESTIONS = [
    {"id":"B01","level":"Basic","topic":"Filtering","title":"Delhi customers",
     "prompt":"Return the first name, last name, and city of customers who live in Delhi.",
     "hint":"Use SELECT with a WHERE filter on city.",
     "solution":"SELECT first_name, last_name, city\nFROM customers\nWHERE city = 'Delhi';",
     "explanation":"WHERE filters rows before the results are returned.",
     "expected_rows":2},
    {"id":"B02","level":"Basic","topic":"Sorting","title":"Highest-value orders",
     "prompt":"Show order_id and amount for all orders, sorted from highest amount to lowest.",
     "hint":"Use ORDER BY amount with descending order.",
     "solution":"SELECT order_id, amount\nFROM orders\nORDER BY amount DESC;",
     "explanation":"ORDER BY sorts the result. DESC places larger values first.",
     "expected_rows":12},
    {"id":"B03","level":"Basic","topic":"Aggregation","title":"Orders per customer",
     "prompt":"Show each customer_id and their total number of orders. Include only customers who have orders.",
     "hint":"GROUP BY customer_id and count rows.",
     "solution":"SELECT customer_id, COUNT(*) AS order_count\nFROM orders\nGROUP BY customer_id\nORDER BY customer_id;",
     "explanation":"GROUP BY creates one group per customer_id; COUNT(*) counts rows in each group.",
     "expected_rows":6},
    {"id":"B04","level":"Basic","topic":"Aggregation","title":"Average order amount",
     "prompt":"Calculate the average order amount, rounded to two decimal places.",
     "hint":"Use AVG() and ROUND().",
     "solution":"SELECT ROUND(AVG(amount), 2) AS average_amount\nFROM orders;",
     "explanation":"AVG computes the mean of non-NULL values; ROUND formats the result to two decimals.",
     "expected_rows":1},
    {"id":"B05","level":"Basic","topic":"Filtering","title":"Delivered orders",
     "prompt":"Return all columns for orders with status 'Delivered'.",
     "hint":"Filter on the status column.",
     "solution":"SELECT *\nFROM orders\nWHERE status = 'Delivered';",
     "explanation":"A string literal is enclosed in single quotes in SQL.",
     "expected_rows":9},
    {"id":"I01","level":"Intermediate","topic":"JOIN","title":"Customer order details",
     "prompt":"Show each order_id, customer full name, order amount, and status.",
     "hint":"Join customers to orders using customer_id. Concatenate first and last names with || in SQLite.",
     "solution":"SELECT o.order_id,\n       c.first_name || ' ' || c.last_name AS customer_name,\n       o.amount,\n       o.status\nFROM orders AS o\nJOIN customers AS c ON c.customer_id = o.customer_id\nORDER BY o.order_id;",
     "explanation":"JOIN combines related rows. The ON clause defines how records match.",
     "expected_rows":12},
    {"id":"I02","level":"Intermediate","topic":"HAVING","title":"Customers spending over 2,000",
     "prompt":"Find customers whose total order amount is greater than 2,000. Show customer_id and total_spend.",
     "hint":"Aggregate with SUM(), then filter groups using HAVING.",
     "solution":"SELECT customer_id, SUM(amount) AS total_spend\nFROM orders\nGROUP BY customer_id\nHAVING SUM(amount) > 2000\nORDER BY total_spend DESC;",
     "explanation":"WHERE filters individual rows; HAVING filters grouped results after aggregation.",
     "expected_rows":4},
    {"id":"I03","level":"Intermediate","topic":"CASE","title":"Classify order sizes",
     "prompt":"Show order_id and amount, plus order_band: 'High' for amount >= 2000, 'Medium' for amount >= 1000, otherwise 'Low'.",
     "hint":"Use CASE WHEN in the SELECT list.",
     "solution":"SELECT order_id, amount,\n       CASE\n         WHEN amount >= 2000 THEN 'High'\n         WHEN amount >= 1000 THEN 'Medium'\n         ELSE 'Low'\n       END AS order_band\nFROM orders\nORDER BY order_id;",
     "explanation":"CASE evaluates conditions in order and returns the result for the first matching condition.",
     "expected_rows":12},
    {"id":"I04","level":"Intermediate","topic":"CTE","title":"Department salary averages",
     "prompt":"Show each department and its average salary, rounded to the nearest whole number, only where the average exceeds 60,000.",
     "hint":"Use GROUP BY and HAVING. ROUND(AVG(salary), 0) works in SQLite.",
     "solution":"SELECT department, ROUND(AVG(salary), 0) AS avg_salary\nFROM employees\nGROUP BY department\nHAVING AVG(salary) > 60000\nORDER BY avg_salary DESC;",
     "explanation":"Aggregate each department, then use HAVING to keep departments whose average salary is above the threshold.",
     "expected_rows":2},
    {"id":"I05","level":"Intermediate","topic":"Subquery","title":"Orders above average",
     "prompt":"Find orders whose amount is greater than the average amount across all orders.",
     "hint":"Compare each order amount with a scalar subquery that returns AVG(amount).",
     "solution":"SELECT order_id, amount\nFROM orders\nWHERE amount > (SELECT AVG(amount) FROM orders)\nORDER BY amount DESC;",
     "explanation":"A scalar subquery can return one value used by the outer query's WHERE condition.",
     "expected_rows":5},
    {"id":"E01","level":"Expert","topic":"Window functions","title":"Rank orders by amount",
     "prompt":"Return order_id, customer_id, amount, and a rank of each order by amount from highest to lowest. Keep ties at the same rank.",
     "hint":"Use RANK() OVER (ORDER BY amount DESC).",
     "solution":"SELECT order_id, customer_id, amount,\n       RANK() OVER (ORDER BY amount DESC) AS amount_rank\nFROM orders\nORDER BY amount_rank, order_id;",
     "explanation":"RANK assigns equal ranks to ties and leaves gaps after tied values.",
     "expected_rows":12},
    {"id":"E02","level":"Expert","topic":"Window functions","title":"Running customer spend",
     "prompt":"For each customer, list their orders by date and calculate cumulative spend in date order.",
     "hint":"Use SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date, order_id).",
     "solution":"SELECT customer_id, order_id, order_date, amount,\n       SUM(amount) OVER (\n         PARTITION BY customer_id\n         ORDER BY order_date, order_id\n         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n       ) AS running_spend\nFROM orders\nORDER BY customer_id, order_date, order_id;",
     "explanation":"PARTITION BY resets the running total for each customer; ORDER BY defines the sequence within each customer.",
     "expected_rows":12},
    {"id":"E03","level":"Expert","topic":"CTE + ranking","title":"Top-paid employee per department",
     "prompt":"Return the highest-paid employee in each department. If there is a tie, return all tied employees.",
     "hint":"Use RANK() partitioned by department and filter rank = 1 in a CTE.",
     "solution":"WITH ranked_employees AS (\n  SELECT employee_id, employee_name, department, salary,\n         RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank\n  FROM employees\n)\nSELECT employee_id, employee_name, department, salary\nFROM ranked_employees\nWHERE salary_rank = 1\nORDER BY department, employee_name;",
     "explanation":"The CTE names the ranked result so it can be filtered in the outer query. RANK preserves ties.",
     "expected_rows":5},
    {"id":"E04","level":"Expert","topic":"Self JOIN","title":"Employee and manager",
     "prompt":"Show every employee and their manager's name. Employees without a manager should still appear.",
     "hint":"Use a LEFT JOIN from employees to employees, matching manager_id to the manager's employee_id.",
     "solution":"SELECT e.employee_name AS employee,\n       m.employee_name AS manager\nFROM employees AS e\nLEFT JOIN employees AS m ON e.manager_id = m.employee_id\nORDER BY e.employee_id;",
     "explanation":"A self join relates rows in the same table. LEFT JOIN keeps employees whose manager_id is NULL.",
     "expected_rows":7},
    {"id":"E05","level":"Expert","topic":"Business analysis","title":"Monthly revenue",
     "prompt":"Calculate monthly revenue from delivered orders only. Return the month as YYYY-MM and revenue, ordered chronologically.",
     "hint":"SQLite supports strftime('%Y-%m', order_date). Filter status before grouping.",
     "solution":"SELECT strftime('%Y-%m', order_date) AS month,\n       ROUND(SUM(amount), 2) AS revenue\nFROM orders\nWHERE status = 'Delivered'\nGROUP BY strftime('%Y-%m', order_date)\nORDER BY month;",
     "explanation":"Filter to delivered orders, group by the month extracted from the date, then sum revenue.",
     "expected_rows":2},
]

# -------------------- Session state --------------------
if "completed" not in st.session_state:
    st.session_state.completed = set()
if "attempts" not in st.session_state:
    st.session_state.attempts = {}
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "show_solution" not in st.session_state:
    st.session_state.show_solution = False
if "current_question" not in st.session_state:
    st.session_state.current_question = "B01"

# -------------------- Sidebar --------------------
st.sidebar.markdown("## ◈ SQL Lab")
st.sidebar.caption("Your hands-on SQL workspace")
st.sidebar.markdown("---")
page = st.sidebar.radio("WORKSPACE", ["Practice Lab", "Explore Data", "Dataset Manager", "Progress & Notes", "About"])
st.sidebar.markdown("---")
st.sidebar.markdown("### Your learning path")
st.sidebar.markdown("🟢 **Basic** · Fundamentals")
st.sidebar.markdown("🟡 **Intermediate** · Joins & subqueries")
st.sidebar.markdown("🔴 **Expert** · Windows & analysis")
st.sidebar.caption("SQL engine: SQLite · Sample data resets each session.")

# -------------------- Header --------------------
st.markdown("""
<div class="hero">
  <div class="eyebrow">SQL PRACTICE WORKSPACE</div>
  <h1>Think in queries.<br>Grow into an analyst.</h1>
  <p>Build real SQL confidence through focused challenges, instant query results, and a clear view of your progress.</p>
</div>
""", unsafe_allow_html=True)

if page == "Practice Lab":
    total = len(QUESTIONS)
    completed_count = len(st.session_state.completed)
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "QUESTIONS", total),
        (c2, "COMPLETED", completed_count),
        (c3, "REMAINING", total-completed_count),
        (c4, "COMPLETION", f"{round(completed_count/total*100)}%"),
    ]:
        with col:
            st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)
    st.progress(completed_count / total)

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        level_filter = st.selectbox("Difficulty", ["All levels", "Basic", "Intermediate", "Expert"])
    with search_col:
        search = st.text_input("Search questions", placeholder="Try JOIN, ranking, revenue…")
    filtered = [q for q in QUESTIONS if (level_filter == "All levels" or q["level"] == level_filter)
                and (search.lower() in (q["title"] + " " + q["topic"] + " " + q["prompt"]).lower())]
    if not filtered:
        st.info("No questions match your search. Try another keyword.")
    else:
        qids = [q["id"] for q in filtered]
        if st.session_state.current_question not in qids:
            st.session_state.current_question = qids[0]
        selected_id = st.selectbox(
            "Choose a question",
            qids,
            index=qids.index(st.session_state.current_question),
            format_func=lambda x: f"{x} · {next(q['title'] for q in QUESTIONS if q['id']==x)}",
        )
        st.session_state.current_question = selected_id
        q = next(q for q in QUESTIONS if q["id"] == selected_id)
        level_icon = {"Basic":"🟢", "Intermediate":"🟡", "Expert":"🔴"}[q["level"]]
        st.markdown(f"### {level_icon} {q['title']}  <span class='tag'>{q['level']}</span> <span class='tag'>{q['topic']}</span>", unsafe_allow_html=True)
        st.markdown(q["prompt"])
        with st.expander("💡 Hint"):
            st.write(q["hint"])

        schema_tab, editor_tab = st.tabs(["📚 Schema reference", "⌨️ SQL editor"])
        with schema_tab:
            st.markdown("**Available tables**")
            st.code("customers(customer_id, first_name, last_name, city, signup_date)\norders(order_id, customer_id, order_date, amount, status)\nemployees(employee_id, employee_name, department, salary, hire_date, manager_id)", language="text")
        with editor_tab:
            default_query = st.session_state.get(f"query_{q['id']}", "")
            sql = st.text_area("Write your SQL query", value=default_query, height=190,
                               placeholder="SELECT ...", key=f"editor_{q['id']}")
            st.session_state[f"query_{q['id']}"] = sql
            run_col, solution_col, reset_col = st.columns([1, 1, 1])
            with run_col:
                run_query = st.button("▶ Run query", type="primary", use_container_width=True)
            with solution_col:
                reveal = st.button("Show solution", use_container_width=True)
            with reset_col:
                clear = st.button("Clear editor", use_container_width=True)

            if clear:
                st.session_state[f"query_{q['id']}"] = ""
                st.rerun()

            if reveal:
                st.session_state.show_solution = not st.session_state.show_solution

            if run_query:
                cleaned = sql.strip()
                if not cleaned:
                    st.warning("Write a query first.")
                elif not cleaned.lower().startswith(("select", "with", "explain")):
                    st.error("For safety, this lab only accepts SELECT-style queries (SELECT, WITH, or EXPLAIN).")
                else:
                    try:
                        conn = get_connection()
                        result = pd.read_sql_query(cleaned, conn)
                        conn.close()
                        st.session_state.attempts[q["id"]] = st.session_state.attempts.get(q["id"], 0) + 1
                        st.session_state.query_history.insert(0, {"id":q["id"], "title":q["title"], "sql":cleaned, "rows":len(result)})
                        st.session_state.query_history = st.session_state.query_history[:20]
                        st.session_state[f"result_{q['id']}"] = result
                        st.session_state[f"ran_{q['id']}"] = True
                        if len(result) == q["expected_rows"]:
                            st.session_state.completed.add(q["id"])
                            st.success(f"Query ran successfully · {len(result)} rows returned. Row count matches the reference result.")
                        else:
                            st.success(f"Query ran successfully · {len(result)} rows returned.")
                            st.caption("Compare the result with the prompt; matching row counts alone do not prove correctness.")
                    except Exception as e:
                        st.error(f"SQL error: {e}")

            if st.session_state.get(f"ran_{q['id']}", False):
                result = st.session_state.get(f"result_{q['id']}")
                if result is not None:
                    st.markdown("#### Query result")
                    st.dataframe(result, use_container_width=True, hide_index=True)
                    st.caption(f"{len(result)} row(s) · {len(result.columns)} column(s)")
            if st.session_state.show_solution:
                st.markdown("#### Reference solution")
                st.code(q["solution"], language="sql")
                st.info(q["explanation"])
        st.markdown("---")
        prev_next = st.columns(2)
        all_ids = [q["id"] for q in filtered]
        current_idx = all_ids.index(q["id"])
        with prev_next[0]:
            if st.button("← Previous question", disabled=current_idx == 0, use_container_width=True):
                st.session_state.current_question = all_ids[current_idx-1]
                st.session_state.show_solution = False
                st.rerun()
        with prev_next[1]:
            if st.button("Next question →", disabled=current_idx == len(all_ids)-1, use_container_width=True):
                st.session_state.current_question = all_ids[current_idx+1]
                st.session_state.show_solution = False
                st.rerun()

elif page == "Explore Data":
    st.markdown("## 🗃️ Explore the sample database")
    st.caption("Get familiar with the tables, fields, and relationships before you start querying.")
    conn = get_connection()
    tabs = st.tabs(["customers", "orders", "employees", "Schema"])
    for tab, table in zip(tabs[:3], ["customers", "orders", "employees"]):
        with tab:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(df)} rows · {len(df.columns)} columns")
    with tabs[3]:
        st.code("""customers
- customer_id (INTEGER, primary key)
- first_name, last_name, city, signup_date

orders
- order_id (INTEGER, primary key)
- customer_id (INTEGER, references customers)
- order_date, amount, status

employees
- employee_id (INTEGER, primary key)
- employee_name, department, salary, hire_date, manager_id""", language="text")
    conn.close()
    st.info("All data is synthetic and created for practice. It is reset when the app session restarts.")

elif page == "Progress & Notes":
    st.markdown("## Your practice progress")
    st.caption("A live snapshot of your SQL practice in this session.")
    completed = st.session_state.completed
    metrics = st.columns(3)
    metrics[0].metric("Completed", len(completed), f"of {len(QUESTIONS)}")
    metrics[1].metric("Queries run", sum(st.session_state.attempts.values()))
    metrics[2].metric("Questions attempted", len(st.session_state.attempts))
    progress_df = pd.DataFrame([
        {"ID":q["id"], "Level":q["level"], "Question":q["title"],
         "Status":"Completed" if q["id"] in completed else ("Attempted" if q["id"] in st.session_state.attempts else "Not started"),
         "Attempts":st.session_state.attempts.get(q["id"], 0)}
        for q in QUESTIONS
    ])
    st.dataframe(progress_df, use_container_width=True, hide_index=True)
    if st.session_state.query_history:
        st.markdown("### Recent queries")
        for item in st.session_state.query_history:
            with st.expander(f"{item['id']} · {item['title']} · {item['rows']} rows"):
                st.code(item["sql"], language="sql")
    st.download_button("⬇ Download progress CSV", progress_df.to_csv(index=False).encode("utf-8"),
                       file_name="sql_practice_progress.csv", mime="text/csv")
    if st.button("Reset progress"):
        st.session_state.completed = set()
        st.session_state.attempts = {}
        st.session_state.query_history = []
        st.session_state.show_solution = False
        st.rerun()

elif page == "Dataset Manager":
    st.markdown("## Dataset manager")
    st.caption("Import related CSV files, inspect their structure, discover likely keys, and query your uploaded data without changing the built-in practice database.")

    data_dir = Path(__file__).resolve().parent / "data" / "uploaded_csv"
    data_dir.mkdir(parents=True, exist_ok=True)

    def _safe_table_name(filename):
        name = Path(filename).stem.lower().strip()
        name = re.sub(r"[^a-z0-9_]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        if not name:
            name = "uploaded_table"
        if name[0].isdigit():
            name = "t_" + name
        return name[:60]

    def _quote_identifier(identifier):
        return '"' + str(identifier).replace('"', '""') + '"'

    def _load_uploaded_tables(folder):
        frames = {}
        for csv_path in sorted(folder.glob("*.csv")):
            table_name = _safe_table_name(csv_path.name)
            # Avoid ambiguous table names if filenames normalize to the same identifier.
            base, suffix, counter = table_name, 2, 2
            while table_name in frames:
                table_name = f"{base}_{counter}"
                counter += 1
            try:
                frames[table_name] = pd.read_csv(csv_path, low_memory=False)
            except Exception as exc:
                st.error(f"Could not read {csv_path.name}: {exc}")
        return frames

    def _likely_keys(frames):
        primary_keys, foreign_keys = {}, []
        for table, frame in frames.items():
            candidates = [c for c in frame.columns if str(c).lower() in {"id", f"{table}_id"} or str(c).lower().endswith("_id")]
            chosen = None
            for col in candidates:
                series = frame[col].dropna()
                if len(series) and series.is_unique:
                    chosen = col
                    break
            primary_keys[table] = chosen
        for child_table, frame in frames.items():
            for col in frame.columns:
                col_lower = str(col).lower()
                if not col_lower.endswith("_id"):
                    continue
                for parent_table, pk in primary_keys.items():
                    if parent_table == child_table or pk is None:
                        continue
                    expected = {f"{parent_table}_id", f"{parent_table.rstrip('s')}_id", str(pk).lower()}
                    if col_lower in expected:
                        foreign_keys.append((child_table, col, parent_table, pk))
                        break
        return primary_keys, foreign_keys

    uploaded = st.file_uploader(
        "Upload one or more CSV files",
        type=["csv"],
        accept_multiple_files=True,
        help="For the Olist dataset, select the CSV files you want to work with, such as orders, customers, order_items, products, payments, and reviews."
    )
    action_col, note_col = st.columns([1, 2])
    with action_col:
        import_clicked = st.button("Import selected CSVs", type="primary", use_container_width=True)
    with note_col:
        st.caption("Imported CSV files are saved locally in the app's data/uploaded_csv folder and remain available after reruns.")

    if import_clicked:
        if not uploaded:
            st.warning("Choose at least one CSV file first.")
        else:
            saved, errors = 0, []
            for file in uploaded:
                try:
                    # Validate before writing so a malformed file does not replace a usable copy.
                    pd.read_csv(file, nrows=5)
                    target = data_dir / Path(file.name).name
                    target.write_bytes(file.getvalue())
                    saved += 1
                except Exception as exc:
                    errors.append(f"{file.name}: {exc}")
            if saved:
                st.success(f"Imported {saved} CSV file(s). They are now available below and will persist on this machine.")
            for error in errors:
                st.error(error)

    frames = _load_uploaded_tables(data_dir)
    if not frames:
        st.info("No CSV datasets imported yet. Upload the Olist CSV files above to get started.")
    else:
        total_rows = sum(len(frame) for frame in frames.values())
        metric_cols = st.columns(3)
        metric_cols[0].metric("CSV tables", len(frames))
        metric_cols[1].metric("Total rows", f"{total_rows:,}")
        metric_cols[2].metric("Total columns", sum(len(frame.columns) for frame in frames.values()))

        primary_keys, foreign_keys = _likely_keys(frames)
        st.markdown("### Imported tables")
        table_names = list(frames.keys())
        selected_table = st.selectbox("Preview table", table_names, key="dataset_preview_table")
        preview_df = frames[selected_table]
        st.dataframe(preview_df.head(100), use_container_width=True, hide_index=True)
        st.caption(f"Showing up to 100 of {len(preview_df):,} rows · {len(preview_df.columns)} columns")

        with st.expander("Column details and inferred data types", expanded=True):
            schema_df = pd.DataFrame({
                "Column": list(preview_df.columns),
                "Inferred type": [str(dtype) for dtype in preview_df.dtypes],
                "Non-null values": [int(preview_df[c].notna().sum()) for c in preview_df.columns],
                "Null values": [int(preview_df[c].isna().sum()) for c in preview_df.columns],
                "Unique values": [int(preview_df[c].nunique(dropna=True)) for c in preview_df.columns],
            })
            st.dataframe(schema_df, use_container_width=True, hide_index=True)

        with st.expander("Relational schema: likely primary and foreign keys", expanded=True):
            st.caption("These are heuristic suggestions based on unique *_id columns and matching table names. Verify them against the dataset documentation before relying on them as constraints.")
            key_rows = []
            for table, frame in frames.items():
                pk = primary_keys.get(table)
                key_rows.append({"Table": table, "Likely primary key": pk or "Not detected", "Rows": len(frame), "Columns": len(frame.columns)})
            st.dataframe(pd.DataFrame(key_rows), use_container_width=True, hide_index=True)
            if foreign_keys:
                st.markdown("**Likely foreign-key relationships**")
                fk_df = pd.DataFrame(foreign_keys, columns=["Child table", "Child column", "Parent table", "Parent key"])
                st.dataframe(fk_df, use_container_width=True, hide_index=True)
            else:
                st.info("No likely foreign-key relationships detected yet. Check table/column naming or define relationships using the source dataset documentation.")

        st.markdown("### Query uploaded tables")
        st.caption("Use SQLite-compatible SQL. Table names are derived from CSV filenames; for example, olist_orders_dataset.csv becomes olist_orders_dataset.")
        default_sql = f'SELECT * FROM "{selected_table}" LIMIT 20;'
        sql = st.text_area("SQL query", value=st.session_state.get("uploaded_dataset_sql", default_sql), height=170, key="uploaded_dataset_sql_editor", placeholder="SELECT ... FROM table_name LIMIT 20;")
        run_col, reset_col = st.columns([1, 1])
        with run_col:
            run_uploaded_query = st.button("Run query on uploaded data", type="primary", use_container_width=True)
        def _reset_uploaded_sql():
            current_table = st.session_state.get("dataset_preview_table", selected_table)
            st.session_state["uploaded_dataset_sql_editor"] = f'SELECT * FROM "{current_table}" LIMIT 20;'

        with reset_col:
            st.button("Reset query", use_container_width=True, on_click=_reset_uploaded_sql)

        if run_uploaded_query:
            cleaned = sql.strip().rstrip(";").strip()
            if not cleaned:
                st.warning("Enter a query first.")
            elif not re.match(r"^(SELECT|WITH|EXPLAIN)\b", cleaned, flags=re.IGNORECASE):
                st.error("For safety, only read-only SELECT, WITH, and EXPLAIN queries are allowed.")
            else:
                conn = sqlite3.connect(":memory:")
                try:
                    for table, frame in frames.items():
                        frame.to_sql(table, conn, index=False, if_exists="replace")
                    # SQLite authorizer blocks writes and schema changes even if hidden inside a CTE.
                    denied_actions = {
                        sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                        sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_CREATE_TABLE,
                        sqlite3.SQLITE_CREATE_TEMP_INDEX, sqlite3.SQLITE_CREATE_TEMP_TABLE,
                        sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_VIEW,
                        sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_VIEW,
                        sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_TABLE,
                        sqlite3.SQLITE_DROP_TEMP_INDEX, sqlite3.SQLITE_DROP_TEMP_TABLE,
                        sqlite3.SQLITE_DROP_TEMP_TRIGGER, sqlite3.SQLITE_DROP_TEMP_VIEW,
                        sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_DROP_VIEW,
                        sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
                        sqlite3.SQLITE_PRAGMA,
                    }
                    def _authorize(action, arg1, arg2, db_name, trigger_name):
                        if action in denied_actions:
                            return sqlite3.SQLITE_DENY
                        return sqlite3.SQLITE_OK
                    conn.set_authorizer(_authorize)
                    result_df = pd.read_sql_query(cleaned, conn)
                    st.success(f"Query executed successfully · {len(result_df):,} row(s) returned.")
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    st.caption(f"{len(result_df):,} row(s) · {len(result_df.columns)} column(s). Preview is rendered by Streamlit; avoid selecting millions of rows at once.")
                except Exception as exc:
                    st.error(f"Query could not be executed: {exc}")
                finally:
                    conn.close()

        with st.expander("File management"):
            st.write("Files currently stored for this app:")
            for csv_path in sorted(data_dir.glob("*.csv")):
                st.write(f"• {csv_path.name} · {csv_path.stat().st_size / 1024:.1f} KB")
            st.caption("Removing files here only affects uploaded CSV copies; it does not remove the built-in sample database or existing interview questions.")
            if st.button("Clear all uploaded CSVs", type="secondary"):
                for csv_path in data_dir.glob("*.csv"):
                    csv_path.unlink(missing_ok=True)
                st.success("Uploaded CSV files removed.")
                st.rerun()

elif page == "About":
    st.markdown("## About SQL Interview Lab")
    st.caption("A lightweight, hands-on environment for building practical SQL skills.")
    st.write("A local, interactive practice environment for aspiring Data Analysts. Run read-only SQL against a small sample database, study hints and solutions, and track progress.")
    st.markdown("### Included")
    st.markdown("- 15 curated questions across Basic, Intermediate, and Expert levels\n- In-browser SQL editor and result tables\n- Search and difficulty filters\n- Hints, reference solutions, and explanations\n- Sample customers, orders, and employees tables\n- Progress dashboard and CSV export")
    st.warning("This educational app runs SQLite in memory. The query editor is restricted to SELECT-style statements; do not expose a production database to an untrusted SQL editor.")
    st.markdown("### SQL dialect")
    st.write("Queries are written for SQLite. Other SQL databases may use different functions or syntax.")

st.sidebar.markdown("---")
st.sidebar.caption("Built for practice · SQLite · Streamlit")
