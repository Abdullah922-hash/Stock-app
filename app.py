import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")


# Load the CSV data
@st.cache_data
def load_data():
    # Load your data from the CSV file
    df = pd.read_csv('https://raw.githubusercontent.com/Abdullah922-hash/Stock-app/main/stockupdated.csv')  # Make sure to replace 'stock_report_feb2025.csv' with your file path
    return df



# Function for login
def show_login_page():
    st.title("Login Page")

    # Create the login form
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Simple validation (you can replace this with your own authentication method)
        if username == "admin" and password == "abc123":
            st.session_state["logged_in"] = True
            st.success("Login successful!")
            st.session_state["login_page_shown"] = False  # Hide the login page
            st.rerun()  # Force the app to rerun and go to main page
            #st.experimental_rerun()  # Rerun to navigate to main app
        else:
            st.error("Invalid credentials")


# Main App Page
def show_main_app_page():
    st.markdown("""
    <h2 style='color: #2a9d8f;'>Inventory Management Application - 10th April 2025</h1>
    """, unsafe_allow_html=True)

    # Load data
    df = load_data()

    # Sidebar filters
    st.sidebar.title('Filters')

    # Filter by location (multi-select)
    location_options = ['All'] + list(df['Location'].unique())  # Add 'All' to the list of locations
    selected_location = st.sidebar.multiselect('Select Location(s)', location_options, default=['All'], key="location_selectbox")

    # Filter by COBRAND (multi-select)
    COBrand_options = ['All'] + list(df['COBrand'].unique())  # Add 'All' to the list of brands
    selected_COBrand = st.sidebar.multiselect('Select COBrand(s)', COBrand_options, default=['All'], key="COBrand_selectbox")

    # Filter by category (multi-select), but it depends on selected COBRAND
    if 'All' not in selected_COBrand:
        category_options = ['All'] + list(df[df['COBrand'].isin(selected_COBrand)]['Category'].unique())  # Filter categories based on COBRAND
    else:
        category_options = ['All'] + list(df['Category'].unique())  # No filter if 'All' is selected for COBRAND
    selected_category = st.sidebar.multiselect('Select Category(s)', category_options, default=['All'], key="category_selectbox")

    # Filter by item, but it should be dependent on selected COBRAND and selected category
    if 'All' not in selected_category:
        item_options = ['All'] + list(df[df['Category'].isin(selected_category) & df['COBrand'].isin(selected_COBrand)]['ItemName'].unique())
    else:
        item_options = ['All'] + list(df[df['COBrand'].isin(selected_COBrand)]['ItemName'].unique())

    selected_item = st.sidebar.multiselect('Select Item(s)', item_options, default=['All'], key='item')


    # Apply filters to the dataframe
    if 'All' not in selected_location:
        df = df[df['Location'].isin(selected_location)]

    if 'All' not in selected_COBrand:
        df = df[df['COBrand'].isin(selected_COBrand)]

    if 'All' not in selected_category:
       df = df[df['Category'].isin(selected_category)]

    # Apply the item filter **after** location and category filters
    if 'All' not in selected_item:
        df = df[df['ItemName'].isin(selected_item)]



# 1st Table

    # Group by 'DesignNo', 'Color', and 'Sizes', and sum the 'NetSales' and 'AvailableforSales'
    df_grouped_sold = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['NetSales'].sum()
    df_grouped_OH = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['AvailableforSales'].sum()

    # Merge the two dataframes on 'DesignNo', 'Color', and 'Sizes'
    df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], how='inner')



    # Sidebar dynamic filter (choose between Quantity or Price)
    filter_type = st.sidebar.radio('Choose Filter Type', ('Quantity', 'Price'), key="filter_type")


    # Quantity or Price grouping logic
    if filter_type == 'Quantity':
        # Group by 'DesignNo', 'Color', 'Sizes', and 'SalesThrough', and sum the 'NetSales' and 'AvailableforSales'
        df_grouped_sold = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['NetSales'].sum()
        df_grouped_OH = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['AvailableforSales'].sum()

        # Merging the two dataframes on 'DesignNo', 'Color', and 'Sizes'
        df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], how='inner')

    elif filter_type == 'Price':
        # Group by 'DesignNo', 'Color', 'Sizes', and 'SalesThrough', and sum the 'SaleAmount' and 'RetailAmount'
        df_grouped_sold = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['SalesAmount'].sum()
        df_grouped_OH = df.groupby(['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], as_index=False)['RetailAmount'].sum()

        # Merging the two dataframes on 'DesignNo', 'Color', and 'Sizes'
        df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes'], how='inner')




    # Create the pivot table with the correct aggregation (based on Quantity or Price)
    if filter_type == 'Quantity':
        df_pivoted = df_merged.pivot_table(
            index=['Barcode', 'ItemName', 'DesignNo', 'Color'], 
            columns='Sizes', 
            values=['NetSales', 'AvailableforSales'],
            aggfunc={'NetSales': 'sum', 'AvailableforSales': 'sum'}
        )
    elif filter_type == 'Price':
        df_pivoted = df_merged.pivot_table(
            index=['Barcode', 'ItemName', 'DesignNo', 'Color'], 
            columns='Sizes', 
            values=['SalesAmount', 'RetailAmount'],
            aggfunc={'SalesAmount': 'sum', 'RetailAmount': 'sum'}
        )
        
        # Round all values in the dataframe to whole numbers, handle NaN values
        df_pivoted = df_pivoted.applymap(lambda x: int(x) if pd.notna(x) else x)


    # Add total columns for NetSales/AvailableforSales or SalesAmount/RetailAmount
    if filter_type == 'Quantity':
        # Add columns for total NetSales and total AvailableforSales
        df_pivoted['Total Bal.'] = df_pivoted.filter(like='AvailableforSales').sum(axis=1)
        df_pivoted['Total Sales'] = df_pivoted.filter(like='NetSales').sum(axis=1)
    
        # Calculate the sum of the relevant columns for 'Quantity'
        total_balance_stock = df_pivoted['Total Bal.'].sum()
        total_net_sales = df_pivoted['Total Sales'].sum()
    
        # Round to whole values (no decimal places)
        df_pivoted['Total Bal.'] = df_pivoted['Total Bal.'].apply(lambda x: int(x))
        df_pivoted['Total Sales'] = df_pivoted['Total Sales'].apply(lambda x: int(x))
        total_balance_stock = int(total_balance_stock)
        total_net_sales = int(total_net_sales)

    elif filter_type == 'Price':
        # Add columns for total SalesAmount and total RetailAmount
        df_pivoted['Total RA'] = df_pivoted.filter(like='RetailAmount').sum(axis=1)
        df_pivoted['Total SA'] = df_pivoted.filter(like='SalesAmount').sum(axis=1)
    
        # Calculate the sum of the relevant columns for 'Price'
        total_retail_amount = df_pivoted['Total RA'].sum()
        total_sales_amount = df_pivoted['Total SA'].sum()
    
        # Round to whole values (no decimal places)
        df_pivoted['Total RA'] = df_pivoted['Total RA'].apply(lambda x: int(x))
        df_pivoted['Total SA'] = df_pivoted['Total SA'].apply(lambda x: int(x))
        total_retail_amount = int(total_retail_amount)
        total_sales_amount = int(total_sales_amount)


    # Reset the index to flatten the pivoted table
    df_pivoted = df_pivoted.reset_index()

    # Display header and some info
    #st.markdown("""
    #    <h2 style='color: #2a9d8f;'>Inventory Management Application - 10th March 2025</h1>
    #    """, unsafe_allow_html=True)

    # Add a separator line for clarity
    st.markdown("---")

    # Show the filtered data with sizes as columns and the performance interpretation
    #st.write(f"Showing data for {selected_location} | {selected_category} | {selected_item}")
    st.write("**Sales and Inventory by Item Name, Design No., Color, and Size**")
    st.dataframe(df_pivoted, use_container_width=True)


    if filter_type == 'Quantity':
        # Display the sum below the table using st.write
        st.write(f"Total Balance Stock: **{total_balance_stock:,.0f}**")
        st.write(f"Total Net Sales: **{total_net_sales:,.0f}**")

    elif filter_type == 'Price':
        # Display the sum below the table using st.write
        st.write(f"Total Retail Amount: **{total_retail_amount:,.2f}**")
        st.write(f"Total Sales Amount: **{total_sales_amount:,.2f}**")



# 2nd Table

    # Step 1: Calculate the sales-to-stock ratio (NetSales / AvailableforSales)
    if filter_type == 'Quantity':
    
        # Step 1: Aggregate the necessary data in one pass
        df_grouped = df.groupby(['Location', 'DesignNo', 'Color', 'Sizes', 'Barcode', 'ItemName'], as_index=False).agg({
            'NetSales': 'sum',
            'AvailableforSales': 'sum'
        })

        # Step 2: Calculate the AvgDaySale (Average Daily Sale) once
        df_grouped['AvgDaySale'] = ((df_grouped['NetSales'] / 90) * 15).round().astype(int)

        # Step 3: Calculate Excess Stock and Quantity to Move
        df_grouped['Excess_Stock'] = np.maximum(df_grouped['AvailableforSales'] - df_grouped['AvgDaySale'], 0)
        df_grouped['Quantity_to_Move'] = np.maximum(df_grouped['AvgDaySale'] - df_grouped['AvailableforSales'], 0)

        # Step 6: Prepare final_data for the second table (Transfers)
        final_data_transfers = []

        # For each barcode, create the transfer table
        for barcode in df_grouped['Barcode'].unique():
            barcode_data = df_grouped[df_grouped['Barcode'] == barcode]
            design_no, color, sizes, item_name = barcode_data[['DesignNo', 'Color', 'Sizes', 'ItemName']].iloc[0]  # Assuming these are the same for all rows

            # Identify the locations with excess stock and quantity to move
            excess_locations = barcode_data[barcode_data['Excess_Stock'] > 0]
            move_locations = barcode_data[barcode_data['Quantity_to_Move'] > 0]

            # Iterate over move locations to generate transfer details
            for _, move_location in move_locations.iterrows():
                required_qty = move_location['Quantity_to_Move']
                move_loc = move_location['Location']

                # For each transfer, find the corresponding excess location
                for _, excess_location in excess_locations.iterrows():
                    excess_qty = excess_location['Excess_Stock']
                    excess_loc = excess_location['Location']

                    # If there is enough excess stock to transfer
                    if excess_qty > 0 and required_qty > 0:
                        transfer_qty = min(excess_qty, required_qty)

                        if transfer_qty > 0.5:
                            # Create a new row for this transfer
                            row = [barcode, item_name, design_no, color, sizes, excess_loc, move_loc, transfer_qty]

                            # Add the row to final data for transfers table
                            final_data_transfers.append(row)

                            # Update excess stock and required quantity
                            excess_locations.loc[excess_location.name, 'Excess_Stock'] -= transfer_qty
                            barcode_data.loc[move_location.name, 'Quantity_to_Move'] -= transfer_qty

                            required_qty -= transfer_qty
                            if required_qty == 0:
                                break  # No need to transfer more from this location

        # Step 7: Create the final DataFrame for transfers
        columns_transfers = ['Barcode', 'ItemName', 'DesignNo', 'Color', 'Sizes', 'From Location', 'To Location', 'Quantity']
        final_df_transfers = pd.DataFrame(final_data_transfers, columns=columns_transfers)

        # Display the transfers table
        st.write("**Stock Transfer Information (Excess Stock -> Location to Move)**")
        # Display the dataframe
        st.dataframe(final_df_transfers, use_container_width=True)

        # Calculate total quantity to move (sum of the 'Quantity' column)
        total_quantity_to_move = final_df_transfers['Quantity'].sum()

        # Display the total quantity to move below the dataframe
        st.write(f"**Total Quantity to Move**: {total_quantity_to_move:.2f}")


# 5th Table 

        # Step 2: Calculate the AvgDaySale (Average Daily Sale) based on DaysInstore condition
        df['AvgDaySale'] = df.apply(
            lambda row: round((row['NetSales'] / row['DaysInStore'] if row['DaysInStore'] < 90 else row['NetSales'] / 90), 2), axis=1
        )



        # First, perform the groupby and aggregation
        df_balance = df.groupby('Barcode').agg({
            'ItemName': lambda x: x.mode()[0],   # Mode (most frequent value) of ItemName
            'DesignNo': lambda x: x.mode()[0],   # Mode (most frequent value) of DesignNo
            'Color': lambda x: x.mode()[0],      # Mode (most frequent value) of Color
            'Sizes': lambda x: x.mode()[0],      # Mode (most frequent value) of Sizes
            'NetSales': 'sum',                   # Sum of NetSales
            'AvailableforSales': 'sum',          # Sum of AvailableforSales
            'AvgDaySale': 'mean',                # Mean of AvgDaySale
            'DaysInStore': 'mean',               # Mean of DaysInStore
        }).reset_index()


        # Ensure DaysInStore mean is rounded to 2 decimal places
        df_balance['DaysInStore'] = df_balance['DaysInStore'].round(2)

        df_balance['AvgDaySale'] = df_balance['AvgDaySale'].round(4)
        
        # Calculate StockDaysLeft
        df_balance['StockDaysLeft'] = df_balance.apply(
            lambda row: round(row['AvailableforSales'] / row['AvgDaySale'], 2) if row['AvgDaySale'] > 0 else 'Sales Not Yet Started', axis=1
        )

        # Update Status based on StockDaysLeft
        df_balance['Status'] = df_balance['StockDaysLeft'].apply(
            lambda x: 'Need Additional Stock' if isinstance(x, (int, float)) and x < 90 else 
                    ('Sales Pending' if x == 'Sales Not Yet Started' else 'No Need')
        )

        # Calculate Need Qty based on Status
        df_balance['Need Qty'] = df_balance.apply(        
            lambda row: round((90 - row['StockDaysLeft']) * row['AvgDaySale'], 2) if row['Status'] == 'Need Additional Stock' and isinstance(row['StockDaysLeft'], (int, float)) and row['StockDaysLeft'] < 90 else 
                        ("Sales Pending - Awaiting Qty" if row['Status'] == 'Sales Pending' else 0), axis=1
        )

        

        st.write("**Inventory Forecast: Stock Days Left & Replenishment Requirements**")
        # Display the dataframe
        st.dataframe(df_balance, use_container_width=True)

        # Calculate total quantity needed (sum of Need Qty where the value is numeric)
        total_qty_needed = df_balance['Need Qty'].apply(
            lambda x: x if isinstance(x, (int, float)) else 0
        ).sum()


        # Display the total quantity needed below the dataframe
        st.write(f"**Total Qty needed to maintain 90 days stock**: {total_qty_needed:.2f}")
        




    elif filter_type == 'Price':
        # Show a message when Price filter is selected
        st.write("Product Redistribution analysis is available only for Quantity-based filtering.")

    else:
        # If no category is selected, prompt the user
        st.write("Please select category")
    
    
    # Check if filter type is Quantity or Price
    if filter_type == 'Quantity':
        # Top-Selling Items Visualization (Quantity)
        st.subheader('Top-Selling Items by Quantity')

        # Check if the filtered dataframe is empty
        if df.empty:
            st.write("No data available for the selected filters.")
        else:
            # Calculate top-selling items based on 'NetSales' (Quantity)
            top_selling = df.groupby('DesignNo')['NetSales'].sum().sort_values(ascending=False).head(10)

            # Create a figure and axis for the plot
            fig, ax = plt.subplots(figsize=(10, 6))  # Customize the figure size

            # Plot the top-selling items as a bar chart
            top_selling.plot(kind='bar', color='green', ax=ax)

            # Set title and labels
            ax.set_title('Top 10 Selling Items (Quantity)')
            ax.set_ylabel('Total Sales')

            # Add values on top of the bars
            for p in ax.patches:
                ax.annotate(f'{p.get_height():,.0f}',  # Display the height of the bar as value
                            (p.get_x() + p.get_width() / 2., p.get_height()),  # Position of the label
                            ha='center', va='center', 
                            fontsize=10, color='black', 
                            xytext=(0, 10), textcoords='offset points')

            # Display the figure using Streamlit
            st.pyplot(fig)


        # Location-wise Sales vs Stock Comparison (Quantity)
        st.subheader('Location-wise Sales vs Stock (Quantity)')

        # Check if the filtered dataframe is empty
        if df.empty:
            st.write("No data available for the selected filters.")
        else:
            # Group the data by 'Location' and sum 'NetSales' and 'AvailableforSales'
            location_comparison = df.groupby('Location')[['NetSales', 'AvailableforSales']].sum()

            # Create a figure and axis for the plot
            fig, ax = plt.subplots(figsize=(10, 6))  # Customize the figure size

            # Define specific colors for AvailableforSales and NetSales
            colors = ['#4CAF50', '#FF9800']  # Green for AvailableforSales, Orange for NetSales

            # Plot the stacked bar chart with specified colors
            location_comparison.plot(kind='bar', ax=ax, color=colors)

            # Set title and labels
            ax.set_title('Sales vs Stock by Location (Quantity)')
            ax.set_ylabel('Quantity')

            # Add values on top of the bars
            for p in ax.patches:
                ax.annotate(f'{p.get_height():,.0f}',  # Display the height of the bar as value
                            (p.get_x() + p.get_width() / 2., p.get_height()),  # Position of the label
                            ha='center', va='center', 
                            fontsize=10, color='black', 
                            xytext=(0, 10), textcoords='offset points')
                
            # Calculate the total sales and retail amount
            total_saleqty = location_comparison['NetSales'].sum()
            total_stock = location_comparison['AvailableforSales'].sum()

            # Add the totals in the upper-right corner
            ax.annotate(f'Total Sales Qty: {total_saleqty:,.2f}', xy=(1, 0.98), xycoords='axes fraction', 
                        ha='right', va='top', fontsize=12, color='green', fontweight='bold')
            ax.annotate(f'Total Stock Qty: {total_stock:,.2f}', xy=(1, 0.94), xycoords='axes fraction', 
                        ha='right', va='top', fontsize=12, color='orange', fontweight='bold')

            # Set legend to be in a consistent order
            ax.legend(['Net Sales', 'Balance Stock'], loc='upper left')

            # Display the figure using Streamlit
            st.pyplot(fig)


    
    elif filter_type == 'Price':
        # Top-Selling Items Visualization (Price)
        st.subheader('Top-Selling Items by Price')

        # Check if the filtered dataframe is empty
        if df.empty:
            st.write("No data available for the selected filters.")
        else:
            # Calculate top-selling items based on 'SalesAmount' (Price)
            top_selling_price = df.groupby('DesignNo')['SalesAmount'].sum().sort_values(ascending=False).head(10)

            # Create a figure and axis for the plot
            fig, ax = plt.subplots(figsize=(10, 6))  # Customize the figure size

            # Plot the top-selling items as a bar chart
            top_selling_price.plot(kind='bar', color='blue', ax=ax)

            # Set title and labels
            ax.set_title('Top 10 Selling Items (Price)')
            ax.set_ylabel('Total Sales Amount')

            # Add values on top of the bars
            for p in ax.patches:
                ax.annotate(f'{p.get_height():,.2f}',  # Display the height of the bar as value (2 decimal points)
                            (p.get_x() + p.get_width() / 2., p.get_height()),  # Position of the label
                            ha='center', va='center', 
                            fontsize=10, color='black', 
                            xytext=(0, 10), textcoords='offset points')

            # Display the figure using Streamlit
            st.pyplot(fig)


        # Location-wise Sales vs Stock Comparison (Price)
        st.subheader('Location-wise Sales vs Stock (Price)')

        # Check if the filtered dataframe is empty
        if df.empty:
            st.write("No data available for the selected filters.")
        else:
            # Group the data by 'Location' and sum 'SalesAmount' and 'RetailAmount'
            location_comparison_price = df.groupby('Location')[['SalesAmount', 'RetailAmount']].sum()

            # Create a figure and axis for the plot
            fig, ax = plt.subplots(figsize=(10, 6))  # Customize the figure size

            # Define specific colors for AvailableforSales and NetSales
            colors = ['#4CAF50', '#FF9800']  # Green for AvailableforSales, Orange for NetSales

            # Plot the stacked bar chart with specified colors
            location_comparison_price.plot(kind='bar', ax=ax, color=colors)

            # Set title and labels
            ax.set_title('Sales vs Stock by Location (Price)')
            ax.set_ylabel('Amount')

            # Add values on top of the bars
            for p in ax.patches:
                ax.annotate(f'{p.get_height():,.2f}',  # Display the height of the bar as value (2 decimal points)
                            (p.get_x() + p.get_width() / 2., p.get_height()),  # Position of the label
                            ha='center', va='center', 
                            fontsize=10, color='black', 
                            xytext=(0, 10), textcoords='offset points')
                
        
            # Calculate the total sales and retail amount
            total_sales = location_comparison_price['SalesAmount'].sum()
            total_retail = location_comparison_price['RetailAmount'].sum()

            # Add the totals in the upper-right corner
            ax.annotate(f'Total Sales Amount: {total_sales:,.2f}', xy=(1, 0.98), xycoords='axes fraction', 
                        ha='right', va='top', fontsize=12, color='green', fontweight='bold')
            ax.annotate(f'Total Retail Amount: {total_retail:,.2f}', xy=(1, 0.94), xycoords='axes fraction', 
                        ha='right', va='top', fontsize=12, color='orange', fontweight='bold')

            # Set legend to be in a consistent order
            ax.legend(['Sales Amount', 'Retail Amount'], loc='upper left')

            # Display the figure using Streamlit
            st.pyplot(fig)



# Check if the user is logged in
def main():
    # Initialize the session state for first time
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # Check session state for login status
    if not st.session_state["logged_in"]:
        # Show login page if not logged in
        show_login_page()
    else:
        # Show main app page if logged in
        show_main_app_page()


if __name__ == "__main__":
    main()
