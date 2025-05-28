import numpy as np
import pandas as pd
import mysql.connector

df1 = pd.read_csv(r"store_sales_1.csv")
df2 = pd.read_csv(r"store_sales_2.csv")
df3 = pd.read_csv(r"store_sales_3.csv")
combined_df = pd.concat([df1, df2, df3], ignore_index=True)

combined_df = combined_df.dropna(subset=["CustomerID"])
combined_df["Qty"] = combined_df["Qty"].fillna(1)

if combined_df["Unit_Price"].isna().any():
    price_mode = combined_df["Unit_Price"].mode()[0]
    combined_df["Unit_Price"] = combined_df["Unit_Price"].fillna(price_mode)

combined_df["Qty"] = combined_df["Qty"].astype(int)
combined_df["Unit_Price"] = combined_df["Unit_Price"].astype(float)
combined_df["SaleDate"] = pd.to_datetime(combined_df["SaleDate"], errors='coerce')

usd_to_omr = 0.385
combined_df["Total_Price_OMR"] = combined_df["Qty"] * combined_df["Unit_Price"] * usd_to_omr
combined_df["Unit_Price_OMR"] = combined_df["Unit_Price"] * usd_to_omr

text_cols = ["Product", "CustomerName", "CustomerID", "StoreID"]
for col in text_cols:
    if col in combined_df.columns:
        combined_df[col] = combined_df[col].astype(str).str.strip().str.title()

if "Product" in combined_df.columns:
    combined_df.rename(columns={"Product": "ProductName"}, inplace=True)

product_df = combined_df[["ProductName"]].drop_duplicates().reset_index(drop=True)
product_df["ProductID"] = product_df.index + 1

if "CustomerName" in combined_df.columns:
    customer_df = combined_df[["CustomerID", "CustomerName"]].drop_duplicates().reset_index(drop=True)
else:
    customer_df = combined_df[["CustomerID"]].drop_duplicates().reset_index(drop=True)
    customer_df["CustomerName"] = None
customer_df["ContactInfo"] = None

store_df = combined_df[["StoreID"]].drop_duplicates().reset_index(drop=True)
store_df["StoreName"] = None
store_df["Location"] = None

combined_df = combined_df.merge(product_df[["ProductID", "ProductName"]], on="ProductName", how="left")

sale_df = combined_df[[
    "ProductID", "CustomerID", "StoreID", "Qty", "Unit_Price", "SaleDate"
]].copy()
sale_df["CurrencyType"] = "OMR"
sale_df.reset_index(inplace=True)
sale_df.rename(columns={"index": "SaleID"}, inplace=True)
sale_df["SaleID"] += 1

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="R95787839r",
    database="Sales_Data"
)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS Sale")
cursor.execute("DROP TABLE IF EXISTS Product")
cursor.execute("DROP TABLE IF EXISTS Customer")
cursor.execute("DROP TABLE IF EXISTS Store")

cursor.execute("""
CREATE TABLE Product (
    ProductID INT PRIMARY KEY,
    ProductName VARCHAR(255)
)
""")

cursor.execute("""
CREATE TABLE Customer (
    CustomerID VARCHAR(50) PRIMARY KEY,
    CustomerName VARCHAR(255),
    ContactInfo VARCHAR(255)
)
""")

cursor.execute("""
CREATE TABLE Store (
    StoreID VARCHAR(50) PRIMARY KEY,
    StoreName VARCHAR(255),
    Location VARCHAR(255)
)
""")

cursor.execute("""
CREATE TABLE Sale (
    SaleID INT PRIMARY KEY,
    ProductID INT,
    CustomerID VARCHAR(50),
    StoreID VARCHAR(50),
    Qty INT,
    Unit_Price FLOAT,
    SaleDate DATETIME,
    CurrencyType VARCHAR(10),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (StoreID) REFERENCES Store(StoreID)
)
""")

product_data = product_df[["ProductID", "ProductName"]].values.tolist()
customer_data = customer_df[["CustomerID", "CustomerName", "ContactInfo"]].values.tolist()
store_data = store_df[["StoreID", "StoreName", "Location"]].values.tolist()

sale_df["SaleDate"] = sale_df["SaleDate"].apply(
    lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(x) else "1900-01-01 00:00:00"
)

sale_data = sale_df[[
    "SaleID", "ProductID", "CustomerID", "StoreID", "Qty", "Unit_Price", "SaleDate", "CurrencyType"
]].values.tolist()



cursor.executemany("INSERT INTO Product (ProductID, ProductName) VALUES (%s, %s)", product_data)
cursor.executemany("INSERT INTO Customer (CustomerID, CustomerName, ContactInfo) VALUES (%s, %s, %s)", customer_data)
cursor.executemany("INSERT INTO Store (StoreID, StoreName, Location) VALUES (%s, %s, %s)", store_data)
cursor.executemany("""
    INSERT INTO Sale (SaleID, ProductID, CustomerID, StoreID, Qty, Unit_Price, SaleDate, CurrencyType)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", sale_data)

conn.commit()
cursor.close()
conn.close()

print(" LOADING IS DONE ")
