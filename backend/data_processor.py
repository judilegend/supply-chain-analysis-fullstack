import pandas as pd
import numpy as np
import os

def process_supply_chain_data(csv_path):
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    
    # 1. KPIs
    total_revenue = float(df['Revenue generated'].sum())
    total_sold = int(df['Number of products sold'].sum())
    avg_price = float(df['Price'].mean())
    avg_defect_rate = float(df['Defect rates'].mean())
    total_stock = int(df['Stock levels'].sum())
    
    # 2. ABC Classification
    # Group by SKU or just use the rows if SKUs are unique
    abc_df = df[['SKU', 'Number of products sold', 'Revenue generated']].copy()
    abc_df = abc_df.sort_values(by='Number of products sold', ascending=False)
    abc_df['cumulative_sales'] = abc_df['Number of products sold'].cumsum()
    total_sales_volume = abc_df['Number of products sold'].sum()
    abc_df['cumulative_share'] = abc_df['cumulative_sales'] / total_sales_volume
    
    def classify_abc(share):
        if share <= 0.80: return 'A'
        if share <= 0.95: return 'B'
        return 'C'
    
    abc_df['ABC_Class'] = abc_df['cumulative_share'].apply(classify_abc)
    
    # Merge back to original df
    df = df.merge(abc_df[['SKU', 'ABC_Class']], on='SKU', how='left')
    
    # 3. Inventory Performance
    # Days of Inventory (DOI)
    # DOI = Stock levels / (Sales per month)
    # Avoid division by zero
    df['DOI'] = df.apply(lambda row: row['Stock levels'] / (row['Number of products sold'] / 30) if row['Number of products sold'] > 0 else 999, axis=1)
    
    # Turnover Rate
    df['Turnover_Rate'] = df.apply(lambda row: row['Number of products sold'] / row['Stock levels'] if row['Stock levels'] > 0 else row['Number of products sold'], axis=1)
    
    # 4. JSON result
    summary = {
        "total_revenue": total_revenue,
        "total_sold": total_sold,
        "avg_price": round(avg_price, 2),
        "avg_defect_rate": round(avg_defect_rate, 2),
        "total_stock": total_stock
    }
    
    inventory_data = df[['Product type', 'SKU', 'Stock levels', 'Number of products sold', 'DOI', 'Turnover_Rate', 'ABC_Class', 'Revenue generated']].to_dict(orient='records')
    
    shipping_data = df.groupby(['Shipping carriers', 'Transportation modes'])['Shipping costs'].mean().reset_index().to_dict(orient='records')
    
    product_type_data = df.groupby('Product type')['Revenue generated'].sum().reset_index().to_dict(orient='records')
    
    # New: Data by Location for the "Map" visualization
    location_data = df.groupby('Location').agg({
        'Revenue generated': 'sum',
        'Number of products sold': 'sum',
        'Stock levels': 'mean'
    }).reset_index().to_dict(orient='records')
    
    # New: Histogram data (e.g., distribution of prices or sales)
    # We'll just return the raw values for the frontend to bin if needed, 
    # or a pre-binned distribution. Let's provide sales distribution.
    sales_hist = df['Number of products sold'].tolist()
    
    return {
        "summary": summary,
        "inventory": inventory_data,
        "shipping": shipping_data,
        "product_types": product_type_data,
        "location_data": location_data,
        "sales_hist": sales_hist,
        "raw_data": df.to_dict(orient='records') # For frontend filtering
    }

if __name__ == "__main__":
    # Test
    data = process_supply_chain_data("../data/raw/supply_chain_data.csv")
    print(data.keys())
