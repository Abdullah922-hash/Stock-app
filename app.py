import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

st.markdown("""
    <style>
        .css-1q7xtu2, .css-1v0mbdj, .css-1ytij9s, .css-ffhzg2 {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


st.set_page_config(layout="wide")


# Load the CSV data
@st.cache_data
def load_data():
    # Load your data from the CSV file
    df = pd.read_csv('stockreport10m.csv')  # Make sure to replace 'stock_report_feb2025.csv' with your file path
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
            #st.session_state["login_page_shown"] = False  # Hide the login page
            st.rerun()  # Force the app to rerun and go to main page
            #st.experimental_rerun()  # Rerun to navigate to main app
        else:
            st.error("Invalid credentials")


# Main App Page
def show_main_app_page():
    st.markdown("""
    <h2 style='color: #2a9d8f;'>Inventory Management Application - 10th March 2025</h1>
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


    # Group by 'DesignNo', 'Color', and 'Sizes', and sum the 'NetSales' and 'AvailableforSales'
    df_grouped_sold = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['NetSales'].sum()
    df_grouped_OH = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['BalanceStock'].sum()

    # Merge the two dataframes on 'DesignNo', 'Color', and 'Sizes'
    df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['DesignNo', 'Color', 'Sizes'], how='inner')



    # Sidebar dynamic filter (choose between Quantity or Price)
    filter_type = st.sidebar.radio('Choose Filter Type', ('Quantity', 'Price'), key="filter_type")


    # Quantity or Price grouping logic
    if filter_type == 'Quantity':
        # Group by 'DesignNo', 'Color', 'Sizes', and 'SalesThrough', and sum the 'NetSales' and 'BalanceStock'
        df_grouped_sold = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['NetSales'].sum()
        df_grouped_OH = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['BalanceStock'].sum()

        # Merging the two dataframes on 'DesignNo', 'Color', and 'Sizes'
        df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['DesignNo', 'Color', 'Sizes'], how='inner')

    elif filter_type == 'Price':
        # Group by 'DesignNo', 'Color', 'Sizes', and 'SalesThrough', and sum the 'SaleAmount' and 'RetailAmount'
        df_grouped_sold = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['SalesAmount'].sum()
        df_grouped_OH = df.groupby(['DesignNo', 'Color', 'Sizes'], as_index=False)['RetailAmount'].sum()

        # Merging the two dataframes on 'DesignNo', 'Color', and 'Sizes'
        df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['DesignNo', 'Color', 'Sizes'], how='inner')




    # Create the pivot table with the correct aggregation (based on Quantity or Price)
    if filter_type == 'Quantity':
        df_pivoted = df_merged.pivot_table(
            index=['DesignNo', 'Color'], 
            columns='Sizes', 
            values=['NetSales', 'BalanceStock'],
            aggfunc={'NetSales': 'sum', 'BalanceStock': 'sum'}
        )
    elif filter_type == 'Price':
        df_pivoted = df_merged.pivot_table(
            index=['DesignNo', 'Color'], 
            columns='Sizes', 
            values=['SalesAmount', 'RetailAmount'],
            aggfunc={'SalesAmount': 'sum', 'RetailAmount': 'sum'}
        )
        
        # Round all values in the dataframe to whole numbers, handle NaN values
        df_pivoted = df_pivoted.applymap(lambda x: int(x) if pd.notna(x) else x)


    # Add total columns for NetSales/BalanceStock or SalesAmount/RetailAmount
    if filter_type == 'Quantity':
        # Add columns for total NetSales and total BalanceStock
        df_pivoted['Total Bal.'] = df_pivoted.filter(like='BalanceStock').sum(axis=1)
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
    st.dataframe(df_pivoted, use_container_width=True)


    if filter_type == 'Quantity':
    # Display the sum below the table using st.write
        st.write(f"Total Balance Stock: **{total_balance_stock}**")
        st.write(f"Total Net Sales: **{total_net_sales}**")

    elif filter_type == 'Price':
    # Display the sum below the table using st.write
        st.write(f"Total Retail Amount: **{total_retail_amount}**")
        st.write(f"Total Sales Amount: **{total_sales_amount}**")


    # Step 1: Calculate the sales-to-stock ratio (NetSales / BalanceStock)
    if filter_type == 'Quantity':
        # Ensure Location is in the merged dataframe
        df_grouped_sold = df.groupby(['Location', 'DesignNo', 'Color', 'Sizes'], as_index=False)['NetSales'].sum()
        df_grouped_OH = df.groupby(['Location', 'DesignNo', 'Color', 'Sizes'], as_index=False)['BalanceStock'].sum()

        # Merge the dataframes on 'Location', 'DesignNo', 'Color', and 'Sizes'
        df_merged = pd.merge(df_grouped_sold, df_grouped_OH, on=['Location', 'DesignNo', 'Color', 'Sizes'], how='inner')

        # Calculate Sales to Stock Ratio
        df_merged['Sales_to_Stock_Ratio'] = np.where(df_merged['BalanceStock'] == 0, df_merged['NetSales'], df_merged['NetSales'] / df_merged['BalanceStock'])

        # Step 2: Identify locations with low stock and high sales (Need stock)
        low_stock_high_sales = df_merged[(df_merged['Sales_to_Stock_Ratio'] > 1) & (df_merged['BalanceStock'] < 10)].sort_values(by='Sales_to_Stock_Ratio', ascending=False)

        # Step 3: Identify locations with high stock and low sales (Excess stock)
        high_stock_low_sales = df_merged[df_merged['Sales_to_Stock_Ratio'] < 1].sort_values(by='Sales_to_Stock_Ratio')

        # Step 4: Calculate the quantity to move (Desired Stock Level - Current Stock) for locations that need restocking
        #desired_stock_level = 3  # You can adjust this threshold based on your needs
        #low_stock_high_sales['Quantity_to_Move'] = desired_stock_level - low_stock_high_sales['BalanceStock']
   
        # Get today's date
        today = datetime.today()
        day_of_month = today.day

        # Calculate the week of the month
        week_of_month = (day_of_month - 1) // 7 + 1  # Calculate which week of the month we are in

        # Adjust desired stock level based on the week of the month
        if week_of_month == 1:
            desired_stock_level = 12
        elif week_of_month == 2:    
            desired_stock_level = 10
        elif week_of_month == 3:    
            desired_stock_level = 6
        else:    
            desired_stock_level = 4

        low_stock_high_sales['Quantity_to_Move'] = desired_stock_level - low_stock_high_sales['BalanceStock']

        # Step 5: Calculate the excess stock for high-stock low-sales locations
        high_stock_low_sales['Excess_Stock'] = high_stock_low_sales['BalanceStock'] - desired_stock_level
        high_stock_low_sales = high_stock_low_sales[high_stock_low_sales['Excess_Stock'] > 0]  # Filter only those with excess stock

        # Step 6: Match excess stock from high-stock low-sales locations to locations that need stock
        # For simplicity, assume that excess stock from each high-stock location will be distributed evenly
        total_excess_stock = high_stock_low_sales['Excess_Stock'].sum()
        total_needed_stock = low_stock_high_sales['Quantity_to_Move'].sum()
  
        st.write("")    

        # Calculate the stock that can be moved from high-stock low-sales locations to low-stock high-sales locations
        if total_excess_stock >= total_needed_stock:
            st.write("**Awesome! We have more than enough stock to meet the demand, but some locations require stock redistribution!**")
            stock_to_move = low_stock_high_sales[['Location', 'Quantity_to_Move']].copy()
        
            # Check if high_stock_low_sales is not empty before trying to access rows
            if not high_stock_low_sales.empty:
                stock_to_move['Stock_Moved_From'] = high_stock_low_sales[['Location']].iloc[0]['Location']  # Assuming stock is moved from the first high-stock location
            else:
                stock_to_move['Stock_Moved_From'] = "Not enough stock"
        
            #st.write(stock_to_move)
        else:
            st.write("**Alert: Stock is insufficient to meet overall demand. Some locations need product reshuffling, and additional stock is required!**")
            stock_to_move = low_stock_high_sales[['Location', 'Quantity_to_Move']].copy()
            stock_to_move['Stock_Moved_From'] = "Not enough stock"
            #st.write(stock_to_move)

        st.write("")
        # Step 7: Display the location-wise comparison for redistribution
        st.subheader('Product Redistribution Based on Sales-to-Stock Ratio')

        # Display locations with low stock but high sales (need stock replenishment)
        if not low_stock_high_sales.empty:
            st.write("**Locations with Low Stock but High Sales (Need Stock Replenishment):**")
            st.dataframe(low_stock_high_sales[['Location', 'DesignNo', 'Color', 'Sizes', 'BalanceStock', 'NetSales', 'Sales_to_Stock_Ratio', 'Quantity_to_Move']], use_container_width=True)

        # Step 8: Provide actionable insights for stock replenishment
        if not low_stock_high_sales.empty:
            st.write("**Actionable Insights**: Move or restock more products to these locations because they are selling well, but they don't have enough stock. This will help prevent stockouts and lost sales.")

        # Display locations with high stock but low sales (Consider redistributing stock)
        if not high_stock_low_sales.empty:
            st.write("**Locations with High Stock but Low Sales (Consider Redistributing Stock):**")
            st.dataframe(high_stock_low_sales[['Location', 'DesignNo', 'Color', 'Sizes', 'BalanceStock', 'NetSales', 'Sales_to_Stock_Ratio', 'Excess_Stock']], use_container_width=True)

        if not high_stock_low_sales.empty:
            st.write("**Actionable Insights**: Consider moving some of the excess stock from these locations to places with higher sales. This helps optimize the inventory and reduces overstocking in less-performing areas.")

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
            # Group the data by 'Location' and sum 'NetSales' and 'BalanceStock'
            location_comparison = df.groupby('Location')[['NetSales', 'BalanceStock']].sum()

            # Create a figure and axis for the plot
            fig, ax = plt.subplots(figsize=(10, 6))  # Customize the figure size

            # Define specific colors for BalanceStock and NetSales
            colors = ['#4CAF50', '#FF9800']  # Green for BalanceStock, Orange for NetSales

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

            # Define specific colors for BalanceStock and NetSales
            colors = ['#4CAF50', '#FF9800']  # Green for BalanceStock, Orange for NetSales

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
