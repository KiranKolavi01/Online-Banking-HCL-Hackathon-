# Frontend — Online Banking System (Streamlit + HTML/CSS)

## Tech Stack
- Python
- Streamlit
- HTML + CSS (minor polishing only)

---

## How to Run
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## File
```
frontend/
└── app.py    # single file — all pages
```

---

## Session State + Page Refresh Fix

```python
# Initialize before anything else — prevents KeyError
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""

# Persist current page in URL so refresh doesn't reset navigation
params = st.query_params
if "page" in params:
    st.session_state["current_page"] = params["page"]
elif "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.query_params["page"] = page_name

# Show auth pages if not logged in
if not st.session_state["user_id"]:
    show_auth()
else:
    show_dashboard()
```

---

## Sign Up Page

```python
# New customer registration
st.title("Create Account")
name     = st.text_input("Full Name")
email    = st.text_input("Email")
phone    = st.text_input("Phone")
address  = st.text_input("Address")
password = st.text_input("Password", type="password")
confirm  = st.text_input("Confirm Password", type="password")
role     = st.selectbox("Role", ["customer", "admin", "support"])

if st.button("Sign Up"):
    if not all([name, email, phone, address, password, confirm]):
        st.error("All fields are required")
    elif password != confirm:
        st.error("Passwords do not match")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters")
    else:
        r = requests.post(f"{API}/auth/signup",
            json={"name": name, "email": email, "phone": phone,
                  "address": address, "password": password, "role": role})
        if r.status_code == 200:
            st.success("Account created. Please Sign In.")
        else:
            st.error(r.json().get("detail", "Signup failed"))

if st.button("Already have an account? Sign In"):
    navigate_to("signin")
```

---

## Sign In Page

```python
# Default page when not logged in
st.title("Sign In")
email    = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Sign In"):
    if not email or not password:
        st.error("Enter email and password")
    else:
        r = requests.post(f"{API}/auth/signin",
            json={"email": email, "password": password})
        if r.status_code == 200:
            d = r.json()
            st.session_state["user_id"] = d["user_id"]
            st.session_state["role"]    = d["role"]
            st.session_state["name"]    = d["name"]
            navigate_to("Dashboard")
            st.rerun()
        else:
            st.error("Invalid email or password")

if st.button("New here? Sign Up"):
    navigate_to("signup")
```

---

## Sidebar

```python
# Shows role-specific pages + sign out button
with st.sidebar:
    st.write(f"Welcome, {st.session_state['name']}")
    st.write(f"Role: {st.session_state['role']}")

    if st.session_state["role"] == "customer":
        pages = ["Dashboard", "My Accounts", "Fund Transfer",
                 "Transaction History", "Service Requests"]
    elif st.session_state["role"] == "admin":
        pages = ["Manage Customers", "Manage Accounts", "All Transactions"]
    else:  # support
        pages = ["Service Requests"]

    for p in pages:
        label = f"→ {p}" if st.session_state["current_page"] == p else p
        if st.button(label):
            navigate_to(p)

    if st.button("Sign Out"):
        for k in ["user_id", "role", "name", "current_page"]:
            st.session_state[k] = ""
        st.query_params.clear()
        st.rerun()
```

---

## Customer Pages

### Dashboard
```python
# Shows account summary and balance
st.title("My Dashboard")
with st.spinner("Loading..."):
    r = requests.get(f"{API}/customer/{st.session_state['user_id']}/accounts")
    if r.status_code == 200:
        accounts = r.json()
        for acc in accounts:
            st.metric(f"{acc['account_type']} — {acc['account_id']}",
                      f"₹ {acc['balance']:.2f}")
    else:
        st.error("Failed to load accounts")
```

### Fund Transfer
```python
# Customer sends money to another account
st.title("Fund Transfer")
from_acc = st.text_input("From Account ID")
to_acc   = st.text_input("To Account ID")
amount   = st.number_input("Amount", min_value=0.01)

if st.button("Transfer"):
    with st.spinner("Processing..."):
        r = requests.post(f"{API}/customer/transfer",
            json={"from_account": from_acc, "to_account": to_acc, "amount": amount})
        if r.status_code == 200:
            d = r.json()
            st.success(f"Transfer successful! Transaction ID: {d['transaction_id']}")
        else:
            st.error(r.json().get("detail", "Transfer failed"))
```

### Transaction History
```python
# Shows all transactions for this customer
st.title("Transaction History")
with st.spinner("Loading..."):
    r = requests.get(f"{API}/customer/{st.session_state['user_id']}/transactions")
    if r.status_code == 200:
        data = r.json()
        if data:
            import pandas as pd
            df = pd.DataFrame(data)
            # Force numeric types before display — prevents N/A bugs
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No transactions found")
    else:
        st.error("Failed to load transactions")
```

### Service Requests
```python
# Customer raises and views service requests
st.title("Service Requests")

with st.expander("Raise New Request"):
    req_type = st.text_input("Type (e.g. card issue, account freeze)")
    desc     = st.text_area("Description")
    if st.button("Submit"):
        r = requests.post(f"{API}/customer/service-request",
            json={"customer_id": st.session_state["user_id"],
                  "type": req_type, "description": desc})
        if r.status_code == 200:
            st.success("Request submitted")
        else:
            st.error("Failed to submit request")

with st.spinner("Loading your requests..."):
    r = requests.get(f"{API}/customer/{st.session_state['user_id']}/service-requests")
    if r.status_code == 200:
        import pandas as pd
        data = r.json()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No service requests found")
    else:
        st.error("Failed to load requests")
```

---

## Admin Pages

### Manage Customers
```python
# Admin adds and views all customers
st.title("Manage Customers")

with st.expander("Add New Customer"):
    name = st.text_input("Name"); email = st.text_input("Email")
    phone = st.text_input("Phone"); address = st.text_input("Address")
    pwd = st.text_input("Password", type="password")
    if st.button("Add Customer"):
        r = requests.post(f"{API}/admin/customers",
            json={"name": name, "email": email, "phone": phone,
                  "address": address, "password": pwd})
        st.success("Customer added") if r.status_code == 200 else st.error("Failed")

with st.spinner("Loading..."):
    r = requests.get(f"{API}/admin/customers")
    if r.status_code == 200:
        import pandas as pd
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
    else:
        st.error("Failed to load customers")
```

### Manage Accounts
```python
# Admin creates bank accounts for customers
st.title("Manage Accounts")

with st.expander("Create Account"):
    cust_id = st.text_input("Customer ID")
    acc_type = st.selectbox("Account Type", ["savings", "current"])
    init_bal = st.number_input("Initial Balance", min_value=0.0)
    if st.button("Create"):
        r = requests.post(f"{API}/admin/accounts",
            json={"customer_id": cust_id, "account_type": acc_type,
                  "initial_balance": init_bal})
        st.success("Account created") if r.status_code == 200 else st.error("Failed")

with st.spinner("Loading..."):
    r = requests.get(f"{API}/admin/accounts")
    if r.status_code == 200:
        import pandas as pd
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
    else:
        st.error("Failed to load accounts")
```

### All Transactions
```python
# Admin views every transaction in the system
st.title("All Transactions")
with st.spinner("Loading..."):
    r = requests.get(f"{API}/admin/transactions")
    if r.status_code == 200:
        import pandas as pd
        data = r.json()
        if data:
            df = pd.DataFrame(data)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No transactions yet")
    else:
        st.error("Failed to load transactions")
```

---

## Support Pages

### Service Requests (Support View)
```python
# Support views and updates all service requests
st.title("Service Requests")

status_filter = st.selectbox("Filter by Status",
    ["", "pending", "in-progress", "resolved"])

with st.spinner("Loading..."):
    params = {}
    if status_filter:
        params["status"] = status_filter
    r = requests.get(f"{API}/support/service-requests", params=params)
    if r.status_code == 200:
        import pandas as pd
        data = r.json()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No requests found")
    else:
        st.error("Failed to load requests")

st.divider()
req_id    = st.text_input("Request ID to update")
new_status = st.selectbox("New Status", ["pending", "in-progress", "resolved"])
if st.button("Update Status"):
    r = requests.put(f"{API}/support/service-requests/{req_id}",
        json={"status": new_status})
    st.success("Updated") if r.status_code == 200 else st.error("Failed")
```

---

## API Config
```python
API = "http://localhost:8000"
```
