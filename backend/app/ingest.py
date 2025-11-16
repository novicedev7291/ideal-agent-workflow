from app.agents.tools.knowledgebase import KnowledgeBase
from services.screen_service import ScreenService


def start_ingesting():
    screen_repo = ScreenService()
    kb = KnowledgeBase(screen_repo=screen_repo)

    kb.ingest_screen(
        title='Home Dashboard',
        chunk='''
## Home Dashboard


### **Screen Description**

The screen represents the **Home Dashboard** of the *OrderSys* Order Management System. It serves as the central control panel that provides a summarized view of the organization’s financial and operational status. The dashboard is designed to present critical insights such as **cash flow**, **receivables**, **payables**, and **project metrics** in a visually intuitive and easily digestible format.
The layout follows a **sidebar navigation + analytics widgets** pattern, emphasizing clarity, accessibility, and actionable information.

![dashboard](dashboard.png)

---

### **Key Features**

#### **Header Bar**

The top header provides global tools and identity elements:

* **System Name (OrderSys):** Displayed on the top-left corner.
* **Search / Quick Access Icons:** Likely used for searching, opening documents, settings, or notifications.
* **Profile Section:** Displays the logged-in user’s avatar, allowing access to account details.
* **Pro Badge:** Indicates the professional version of the system or advanced feature access.

---

#### **Cash Flow Overview**

A graphical summary representing **cash movement across months**:

* **Bar Graph:** Displays monthly inflows and outflows, helping users track financial performance trends.
* **Balance Indicator:** Highlights total cash surplus/deficit (e.g., “+12,856.14”).
* **Time Filter (Dropdown):** Allows selection of data range (e.g., Year, Quarter, Month).

This feature enables real-time monitoring of financial health at a glance.

---

#### **Total Receivables**

Provides a snapshot of **amounts owed to the business**:

* **Progress Bar:** Visual indicator of total unpaid invoices.
* **Total Value:** Displays combined unpaid invoice value (e.g., $34,291).
* **Breakdown:** Differentiates between *On-time* and *Overdue* receivables with clear numeric values.

This helps identify potential delays or overdue payments.

---

#### **Total Payables**

Displays **outstanding amounts owed by the business**:

* **Progress Bar:** Represents total unpaid bills.
* **Total Value:** Shows combined outstanding payables (e.g., $14,500).
* **Breakdown:** Segregates *On-time* and *Overdue* payments to aid in cash flow management.

This section helps users forecast payment obligations.

---

#### **Cash Flow Data**

Summarizes **cash position and movement** details:

* **Opening Cash Balance:** Amount available at the start of the period (e.g., $20,000).
* **Incoming Cash:** Total inflows during the period (e.g., +$79,490).
* **Outgoing Cash:** Total expenses/outflows (e.g., -$17,320).
* **Net Flow:** Derived automatically to show overall liquidity status.

It offers transparency in financial operations and assists in decision-making.

        ''',
        imgs=['data/raw/dashboard.png']
    )

    kb.ingest_screen(
        title='Product List',
        chunk='''
## **Product List**

The screen represents the **Product List** view of an **Order Management System** called *OrderSys*. It serves as a centralized dashboard for managing the catalog of products available within the system. The interface is designed with a clean and structured layout that allows users to view, update, and organize product details efficiently. The main focus is on providing quick access to key product information such as name, description, version, and update status.

The layout follows a **sidebar navigation + main content panel** design, enabling intuitive movement between system modules like Products, Orders, Vendors, and Sales.

![product-list](product-list.png)
---

### **Key Features**

#### **Header Bar**

The top bar provides global application controls:

* **Application Title (OrderSys):** Positioned at the top-left, identifies the system.
* **Search Bar:** Allows quick search within the product catalog.
* **Settings (Gear Icon):** Opens configuration or system preferences.
* **Add Product Button:** Prominent button for adding a new product entry.
* **User Profile Icon:** Displays the logged-in user’s profile with access to account or logout options.
* **Other Icons (Documents, Help, etc.):** Quick links for documentation, support, or notifications.

---

#### **Product List Table**

Central component of the screen displaying a structured list of products with the following columns:

* **Checkbox:** Allows selection of individual or multiple products for bulk operations.
* **Product:** Displays product names (e.g., BizHub, CarePro, Maven).
* **Description:** Short summary describing each product’s purpose or function.
* **Version:** Indicates the current software/product version.
* **Update:** Visual indicator showing whether the product is up-to-date (✔) or requires an update (✖).

This grid helps users quickly identify product status, version information, and manage updates.

---

#### **Bulk & Inline Operations**

* **Checkbox Selection:** Supports multi-select for performing bulk operations such as delete, update, or export.
* **Update Indicators:** Provide visual cues about product status at a glance, promoting proactive maintenance.
* **Add Product Button:** Enables users to open a form/modal for registering new product details.

''',
        imgs=['data/raw/product-list.png']
    )

    kb.ingest_screen(
        title='Add Product',
        chunk='''
## **Add Product Screen**

This screen represents the **Add New Product** interface of the *OrderSys* Order Management System. It enables users to create and register a new product (either goods, services, or other items) within the product catalog. The interface is designed with a two-column form layout that separates **product details**, **sales information**, and **purchase information**, making data entry structured and efficient.

The layout ensures clarity and logical grouping of fields for easy product onboarding and financial mapping.

![add-product](add-product.png)
---

### **Key Features**

#### **Product Creation Form**

This is the central part of the screen, designed to capture detailed product information.

##### **a. Product Type Selection**

Radio buttons allow users to specify whether the new entry is:

* **Service** (non-tangible offering),
* **Goods** (physical item), or
* **Other** (custom type).

##### **b. Basic Product Details**

Fields to describe the product’s identity and categorization:

* **Product Name:** Name or title of the product.
* **Type:** Classification or sub-category (e.g., hardware, software).
* **Item Number:** Unique SKU or identifier for internal tracking.
* **Source:** Origin of the product (e.g., vendor or department).
* **Tax (%):** Applicable tax rate for this product.
* **Description:** Brief textual summary describing the product’s purpose or attributes.
* **Amount:** Default or base amount for accounting or pricing.

These inputs ensure that every product is clearly defined and uniquely traceable.

---

#### **Sales Information**

A structured section to define details related to selling the product:

* **Selling Price ($):** Default sales price of the item.
* **Account:** Linked accounting ledger for revenue recognition.
* **Tax (%):** Tax rate applicable to product sales (can differ from purchase tax).

This section directly affects how the system records and reports revenue.

---

#### **Purchase Information**

Captures cost and accounting details for procurement:

* **Cost Price ($):** The buying or manufacturing cost.
* **Account:** Accounting ledger for expense tracking.

These values help the system compute profit margins and maintain accurate expense records.

---

#### **Action Buttons**

Located at the bottom of the form, two key action controls are provided:

* **List New Product:** Saves and registers the product into the system database.
* **Cancel Action:** Discards unsaved changes and exits the product creation screen.

These provide users control over data submission and workflow navigation.
''',
        imgs=['data/raw/add-product.png']
    )