
# 🌿 Nature Counter — Journal Entry App

A Streamlit-based application for recording and managing Nature Counter journal entries.  
This app allows authorized users to log time spent in nature along with location, duration, and activity details.

---

## 📁 Project Structure

### **Pages**
- 📓 **Journal-Entry.py** — Main journal entry submission form  
- (Additional pages can be added inside the `pages/` folder)

---

## 🌐 Live Application

You can access the production Streamlit app here:

🔗 **https://nc-app.streamlit.app/**

> ⚠️ *Only authorized users can log in.*  
> Access permissions are managed using Google Sheets (via `permissions_sheet_id` stored in Streamlit secrets).

---

## 🛠 Running the App Locally

Follow the steps below to run the app on your local machine.

### **1️⃣ Clone this repository**
```bash
git clone https://github.com/NcReportAdmin/nc-app-prod
cd nc-app-prod
```

### **2️⃣ Create local secrets file**

Streamlit loads sensitive data from:

```
.streamlit/secrets.toml
```

Create this file on your local machine:

- In VS Code, right-click the project → **New Folder** → name it `.streamlit`
- Inside `.streamlit`, create a new file named `secrets.toml`
- Paste the same secrets used in your Streamlit Cloud deployment  
  *(Google Service Account, sheet IDs, etc.)*

Make sure `.streamlit/secrets.toml` is **NOT committed to GitHub** (add it to `.gitignore`).

---

### **3️⃣ Install dependencies**

```bash
pip install -r requirements.txt
```

---

### **4️⃣ Run the application**

```bash
streamlit run NC-Generic-Login-v1-Secure.py
```
---

## 🧩 Notes for developers

- This app requires a valid **Google Service Account** with access to:
  - Permission sheet
  - Journal data sheet
  - Other sheets defined in `secrets.toml`
- All journal entries are automatically written to the connected Google Sheet.

---
