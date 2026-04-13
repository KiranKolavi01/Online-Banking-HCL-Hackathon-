import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="Online Banking System")

API = "http://localhost:8000"

def apply_theme():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Michroma&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&display=swap');

/* Main body background - Dark mode gradient */
.stApp { 
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif; 
    color: #f8fafc;
}

/* Headers */
h1, h2, h3 { 
    font-family: 'Outfit', sans-serif !important;
    background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important; 
    letter-spacing: -0.02em !important; 
    line-height: 1.2 !important;
    margin-bottom: 1.5rem !important;
}

/* Sidebar - Glassmorphism */
[data-testid="stSidebar"] { 
    background: rgba(15, 23, 42, 0.45) !important; 
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important; 
    padding-top: 1rem;
}
[data-testid="stSidebarNav"] { display: none !important; }

/* Metrics - Glassmorphism cards */
[data-testid="stMetricValue"] { 
    color: #f8fafc !important; 
    font-weight: 800 !important; 
    font-size: 2.5rem !important;
    letter-spacing: -0.04em !important;
    text-shadow: 0 2px 10px rgba(96, 165, 250, 0.3);
}
[data-testid="stMetricLabel"] { 
    color: #94a3b8 !important; 
    font-weight: 700 !important; 
    font-size: 0.75rem !important; 
    text-transform: uppercase !important; 
    letter-spacing: 0.15em !important; 
}
[data-testid="stMetric"] { 
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px);
    padding: 24px !important; 
    border-radius: 16px !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
[data-testid="stMetric"]:hover { 
    transform: translateY(-5px) scale(1.02);
    border-color: rgba(96, 165, 250, 0.6) !important;
    box-shadow: 0 15px 35px 0 rgba(96, 165, 250, 0.2) !important;
    background: rgba(255, 255, 255, 0.08) !important;
}

/* Dividers */
hr { border-bottom: 1px solid rgba(255,255,255,0.1) !important; margin: 2.5rem 0 !important; }

/* Interactive Modern Buttons with Micro-animations */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 12px !important; 
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px -2px rgba(139, 92, 246, 0.3) !important;
    width: 100%;
}
.stButton > button * {
    color: #ffffff !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 20px -5px rgba(139, 92, 246, 0.5) !important;
    border-color: rgba(255,255,255,0.5) !important;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
}

/* Base text overrides */
.stMarkdown, .stText, p, span, div {
    color: #f1f5f9;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Dropdowns and Inputs */
.stTextInput > div > div > input, 
.stNumberInput > div > div > input,
.stSelectbox > div > div > div,
.stPasswordInput > div > div > input {
    background-color: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #f8fafc !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.2) !important;
}
.stTextInput > div > div > input:focus, 
.stNumberInput > div > div > input:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3) !important;
}

/* Fix for Selectbox Dropdown Menu Options Visibility */
[data-baseweb="popover"] > div {
    background-color: #1e293b !important;
}
ul[data-baseweb="menu"] {
    background-color: #1e293b !important;
}
li[data-baseweb="menu"] {
    background-color: transparent !important;
    color: #f8fafc !important;
}
li[data-baseweb="menu"]:hover {
    background-color: #3b82f6 !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

apply_theme()

# Initialize session state from query parameters if available to persist across refresh
params = st.query_params

for key in ["user_id", "role", "name"]:
    if key in params:
        st.session_state[key] = params[key]
    elif key not in st.session_state:
        st.session_state[key] = ""

if "page" in params:
    st.session_state["current_page"] = params["page"]
elif "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name
    st.query_params["page"] = page_name

def show_auth():
    if st.session_state.get("current_page") == "signup":
        # New customer registration
        st.title("Create Account")
        name     = st.text_input("Full Name")
        email    = st.text_input("Email")
        phone    = st.text_input("Phone", max_chars=10)
        address  = st.text_input("Address")
        password = st.text_input("Password", type="password")
        confirm  = st.text_input("Confirm Password", type="password")
        role     = st.selectbox("Role", ["customer", "support"])

        if st.button("Sign Up"):
            if not all([name, email, phone, address, password, confirm]):
                st.error("All fields are required")
            elif password != confirm:
                st.error("Passwords do not match")
            elif not phone.isdigit() or len(phone) != 10:
                st.error("Phone number must be exactly 10 digits")
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
            st.rerun()  # Kept here as it effectively triggers reload for page navigation if not handled inherently in navigate_to, though FRONTEND.md omits it for signup redirect. Wait, let me maintain strict equivalence to frontend.md where possible.

    else:
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
                    
                    st.query_params["user_id"] = d["user_id"]
                    st.query_params["role"]    = d["role"]
                    st.query_params["name"]    = d["name"]
                    
                    navigate_to("Dashboard")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

        if st.button("New here? Sign Up"):
            navigate_to("signup")
            st.rerun() 

def show_dashboard():
    # Shows role-specific pages + sign out button
    with st.sidebar:
        st.write(f"Welcome, {st.session_state['name']}")
        st.write(f"Role: {st.session_state['role']}")

        if st.session_state["role"] == "customer":
            pages = ["Dashboard", "My Accounts", "Fund Transfer",
                     "Transaction History", "Service Requests"]
        elif st.session_state["role"] == "admin":
            pages = ["Manage Customers", "Admin Panel", "Manage Accounts", "All Transactions"]
        else:  # support
            pages = ["Service Requests"]

        for p in pages:
            label = f"→ {p}" if st.session_state.get("current_page") == p else p
            if st.button(label):
                navigate_to(p)
                st.rerun() 

        if st.session_state.get("confirm_signout"):
            st.warning("Are you sure you want to sign out?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes"):
                    for k in ["user_id", "role", "name", "current_page", "confirm_signout"]:
                        if k in st.session_state:
                            st.session_state[k] = ""
                    st.query_params.clear()
                    st.rerun()
            with c2:
                if st.button("No"):
                    st.session_state["confirm_signout"] = False
                    st.rerun()
        else:
            if st.button("Sign Out"):
                st.session_state["confirm_signout"] = True
                st.rerun()

    current_page = st.session_state.get("current_page")
    role = st.session_state.get("role")

    if role == "customer":
        if current_page == "Dashboard":
            # Shows account summary and balance
            st.title("My Dashboard")
            with st.spinner("Loading..."):
                r = requests.get(f"{API}/customer/{st.session_state['user_id']}/accounts")
                if r.status_code == 200:
                    accounts = r.json()
                    if accounts:
                        total_balance = sum(acc['balance'] for acc in accounts)
                        st.metric("Total Net Balance", f"₹ {total_balance:,.2f}")
                        st.divider()
                        st.subheader("Account Breakdown")
                        
                        cols = st.columns(len(accounts) if len(accounts) < 4 else 3)
                        for idx, acc in enumerate(accounts):
                            with cols[idx % len(cols)]:
                                st.metric(f"{acc['account_type'].upper()} — {acc['account_id']}",
                                          f"₹ {acc['balance']:,.2f}")
                    else:
                        st.info("You do not have any active bank accounts.")
                else:
                    st.error("Failed to load accounts")
        
        elif current_page == "My Accounts":
            st.title("My Accounts")
            with st.spinner("Loading accounts..."):
                r = requests.get(f"{API}/customer/{st.session_state['user_id']}/accounts")
                if r.status_code == 200:
                    accounts = r.json()
                    if accounts:
                        df = pd.DataFrame(accounts)
                        st.dataframe(df, width='stretch')
                    else:
                        st.info("No accounts found. Please contact an admin to create an account.")
                else:
                    st.error("Failed to load accounts")

        elif current_page == "Fund Transfer":
            # Customer sends money to another account
            st.title("Fund Transfer")
            from_acc = st.text_input("From Account ID")
            to_acc   = st.text_input("To Account ID")
            amount   = st.number_input("Amount", min_value=0.01)

            if st.button("Transfer"):
                with st.spinner("Processing..."):
                    r = requests.post(f"{API}/customer/transfer",
                        json={"customer_id": int(st.session_state['user_id']), "from_account": from_acc, "to_account": to_acc, "amount": amount})
                    if r.status_code == 200:
                        d = r.json()
                        st.success(f"Transfer successful! Transaction ID: {d['transaction_id']}")
                    else:
                        st.error(r.json().get("detail", "Transfer failed"))

        elif current_page == "Transaction History":
            # Shows all transactions for this customer
            st.title("Transaction History")
            with st.spinner("Loading..."):
                r = requests.get(f"{API}/customer/{st.session_state['user_id']}/transactions")
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        df = pd.DataFrame(data)
                        # Force numeric types before display — prevents N/A bugs
                        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                        st.dataframe(df, width='stretch')
                    else:
                        st.info("No transactions found")
                else:
                    st.error("Failed to load transactions")

        elif current_page == "Service Requests":
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
                    data = r.json()
                    if data:
                        st.dataframe(pd.DataFrame(data), width='stretch')
                    else:
                        st.info("No service requests found")
                else:
                    st.error("Failed to load requests")

    elif role == "admin":
        if current_page == "Manage Customers":
            # Admin adds and views all customers
            st.title("Manage Customers")

            with st.expander("Add New Customer"):
                name = st.text_input("Name"); email = st.text_input("Email")
                phone = st.text_input("Phone", max_chars=10); address = st.text_input("Address")
                pwd = st.text_input("Password", type="password")
                if st.button("Add Customer"):
                    if not phone.isdigit() or len(phone) != 10:
                        st.error("Phone number must be exactly 10 digits")
                    else:
                        r = requests.post(f"{API}/admin/customers",
                            json={"name": name, "email": email, "phone": phone,
                                  "address": address, "password": pwd})
                        if r.status_code == 200:
                            st.success("Customer added")
                        else:
                            st.error(r.json().get("detail", "Failed"))

            with st.spinner("Loading..."):
                r = requests.get(f"{API}/admin/customers")
                if r.status_code == 200:
                    st.dataframe(pd.DataFrame(r.json()), width='stretch')
                else:
                    st.error("Failed to load customers")

        elif current_page == "Admin Panel":
            st.title("Admin Panel")
            st.subheader("Create Bank Account")

            cust_id = st.number_input("Customer ID", min_value=1, step=1)
            acc_type = st.selectbox("Account Type", ["savings", "current"], key="admin_panel_acctype")
            bal = st.number_input("Balance", min_value=0.0, key="admin_panel_balance")

            if st.button("Create API Request"):
                with st.spinner("Processing..."):
                    r = requests.post(f"{API}/admin/accounts",
                        json={"customer_id": int(cust_id), "account_type": acc_type, "balance": bal})
                    if r.status_code == 200:
                        d = r.json()
                        st.success(f"Account successfully created! ID: {d.get('account_id')}")
                    else:
                        st.error(r.json().get("detail", "Failed to create account"))

        elif current_page == "Manage Accounts":
            # Admin creates bank accounts for customers
            st.title("Manage Accounts")

            with st.expander("Create Account"):
                cust_id = st.number_input("Customer ID", min_value=1, step=1, key="manage_accounts_cust_id")
                acc_type = st.selectbox("Account Type", ["savings", "current"])
                init_bal = st.number_input("Initial Balance", min_value=0.0)
                if st.button("Create"):
                    r = requests.post(f"{API}/admin/accounts",
                        json={"customer_id": int(cust_id), "account_type": acc_type,
                              "balance": float(init_bal)})
                    if r.status_code == 200:
                        st.success("Account created")
                    else:
                        st.error("Failed")

            with st.spinner("Loading..."):
                r = requests.get(f"{API}/admin/accounts")
                if r.status_code == 200:
                    st.dataframe(pd.DataFrame(r.json()), width='stretch')
                else:
                    st.error("Failed to load accounts")

        elif current_page == "All Transactions":
            # Admin views every transaction in the system
            st.title("All Transactions")
            with st.spinner("Loading..."):
                r = requests.get(f"{API}/admin/transactions")
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        df = pd.DataFrame(data)
                        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                        st.dataframe(df, width='stretch')
                    else:
                        st.info("No transactions yet")
                else:
                    st.error("Failed to load transactions")

    elif role == "support":
        if current_page == "Service Requests":
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
                    data = r.json()
                    if data:
                        st.dataframe(pd.DataFrame(data), width='stretch')
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
                if r.status_code == 200:
                    st.success("Updated")
                else:
                    st.error("Failed")

# Show auth pages if not logged in
if not st.session_state["user_id"]:
    show_auth()
else:
    show_dashboard()
