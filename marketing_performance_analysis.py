# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

visits = pd.read_csv('visits_log_us.csv')
orders = pd.read_csv('orders_log_us.csv')
costs = pd.read_csv('costs_us.csv')

visits['End Ts'] = pd.to_datetime(visits['End Ts'])
visits['Start Ts'] = pd.to_datetime(visits['Start Ts'])

orders['Buy Ts'] = pd.to_datetime(orders['Buy Ts'])

costs['dt'] = pd.to_datetime(costs['dt'])

"""#  Reports and metrics

## 1. Visits
"""

# New columns for the analysis
visits['Session Year'] = visits['Start Ts'].dt.isocalendar().year
visits['Session Month'] = visits['Start Ts'].dt.month
visits['Session Week'] = visits['Start Ts'].dt.isocalendar().week
visits['Session Date'] = visits['Start Ts'].dt.date

# 1.How many people use the platform each day, week, month?
dau_total = visits.groupby('Session Date').agg({
    'Uid':'nunique'
}).mean()

wau_total = visits.groupby(['Session Year', 'Session Week']).agg({
    'Uid':'nunique'
}).mean()

mau_total = visits.groupby(['Session Year','Session Month']).agg({
    'Uid':'nunique'
}).mean()

print(f'Usuarios activos diarios {dau_total.iloc[0]:.2f}')
print(f'Usuarios activos semanales: {wau_total.iloc[0]:.2f}')
print(f'Usuarios activos mensuales: {mau_total.iloc[0]:.2f}')

# 2.How mny sessions daily? 
sessions_per_user_daily = visits.groupby('Session Date').agg({
    'Uid':['count', 'nunique']
})
sessions_per_user_daily.columns = ['N Sessions', 'N Users']

sessions_per_user_daily['Sessions Per User'] = sessions_per_user_daily['N Sessions'] / sessions_per_user_daily['N Users']

avg_sessions_daily = sessions_per_user_daily['Sessions Per User'].mean()

print(sessions_per_user_daily.head(10))
print()
print(f'On average there are {avg_sessions_daily:.2f} per day')
print()

# 3. Duration of every session:
visits['ASL'] = (visits['End Ts'] - visits['Start Ts']).dt.seconds
visits['ASL'].hist(bins=50, color='skyblue')
plt.title('Duration of every session per user')
plt.tight_layout()
plt.savefig("figures/hist_duration_session_user.png", dpi=150)
plt.close()


#  Since the distribution is not normal, we need to calculate the mode
asl = visits['ASL'].mode()
print()
print(f'Average session time is {asl.iloc[0]} seconds.')
print()

# How ofthe do users return?
# sticky factor = dau / wau, sticky factor = wau / mau

daily_sticky_factor = (dau_total / wau_total) * 100
weekly_sticky_factor = (wau_total / mau_total) * 100

print()
print(f'{daily_sticky_factor.iloc[0]:.2f}% of weekly users return every day.')
print(f'El {weekly_sticky_factor.iloc[0]:.2f}% of monthly users return every week')
print()

"""## 2. Sales
### KPI Analysis

"""

# When do people start buying?
# Análisis de KPI: time elapsed between registration and conversion 
# KPI Analysis: 

first_session_date = visits.groupby('Uid')[
    'Session Date'
].min()
first_session_date.name='First Session Date'

visits = visits.merge(first_session_date, on='Uid')

# Buy Date column created
orders['Buy Date'] = orders['Buy Ts'].dt.date
first_buy_date = orders.groupby('Uid')['Buy Date'].min()
first_buy_date.name='First Buy Date'
orders = orders.merge(first_buy_date, on='Uid')

# First session columns created
first_session_year = visits.groupby('Uid')['Session Year'].min()
first_session_month = visits.groupby('Uid')['Session Month'].min()

# Add columns directly on the df
visits['First Session Year'] = visits['Uid'].map(first_session_year)
visits['First Session Month'] = visits['Uid'].map(first_session_month)

print()
print(visits)
print()

conversion = orders[['Uid', 'First Buy Date']].merge(
    visits[['Uid', 'First Session Date', 'First Session Month', 'First Session Year', 'Source Id']],
    on='Uid',
    how='left'
)[['Uid', 'First Session Date', 'First Session Month', 'First Session Year', 'First Buy Date', 'Source Id']].drop_duplicates().reset_index(drop=True)

conversion['First Buy Date'] = pd.to_datetime(conversion['First Buy Date'])
conversion['First Session Date'] = pd.to_datetime(conversion['First Session Date'])
conversion['Conversion Time'] = conversion['First Buy Date'] - conversion['First Session Date']
conversion['Conversion Time Days'] = conversion['Conversion Time'].dt.days

print()
print(conversion)
print()

# Chart to show the cohort with the best conversion rate
cohorts_conversion = conversion.groupby(['First Session Year', 'First Session Month']).agg({
    'Conversion Time Days':'mean'
}).reset_index()

def cohorts_plot_month_year(df, year, label, first_session_year, first_session_month, value):
    plot = df[df[first_session_year] == year]
    return sns.lineplot(data=plot, x= first_session_month, y= value, label=label)

cohorts_plot_month_year(cohorts_conversion, 2017, 2017, 'First Session Year', 'First Session Month', 'Conversion Time Days')
cohorts_plot_month_year(cohorts_conversion, 2018, 2018, 'First Session Year', 'First Session Month', 'Conversion Time Days')

plt.title('Conversion Time per Cohort Between 2017-2018')
plt.xlabel('Cohort Month')
plt.ylabel('Conversion Time (Days)')
plt.legend()
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/conversion_time_per_cohort.png", dpi=150)
plt.close()

print()

print(cohorts_conversion.sort_values(by='Conversion Time Days'))
print()

"""The cohort that took the least amount of time to become a customer is the May 2018 cohort (0.83 days). This means that, on average, customers in this cohort made their first purchase on the same day as their first visit. This cohort is also the most recent for which we have data.

It is also evident that the cohorts between January and September 2017 took the longest to become customers (between 85 and 14 days). This means that, on average, they took between two months and two weeks to make their first purchase.

""
"""


# Chart to show the marketing source with the best conversion
conversion['Conversion Time Days'] = conversion['Conversion Time'].dt.days

marketing_source_conversion = conversion.groupby('Source Id').agg({
    'Conversion Time Days': 'mean'
}).reset_index()

palette = {
    '1': '#FE4A49',
    '2': '#2AB7CA',
    '3': '#FED766',
    '4': '#843B62',
    '5': '#C2EABA',
    '6': '#51344D',
    '7': '#EB6534',
    '8': '#3F88C5',
    '9': '#D4ADCF',
    '10': '#EB6534'
}

sns.barplot(data=marketing_source_conversion, x='Source Id', y='Conversion Time Days', palette = palette)
plt.title('Average Time of Conversion per Marketing Source')
plt.xlabel('Source')
plt.ylabel('Days')
plt.legend([],[], frameon=False)
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/conversion_time_marketing_channel.png", dpi=150)
plt.close()
print()
print(marketing_source_conversion)

"""Marketing channel 7 has a conversion time of 0 days. While this could indicate good performance, suggesting that all users of this channel make their first purchase on the same day, it could also indicate something else is amiss with the data, requiring further investigation."""

"""The channel used by users who convert most quickly is channel 5, with an average conversion time of 21 days. The least effective is channel 9, where users take up to 35 days to become customers. However, it's important to also evaluate the number of conversions to reach a more accurate conclusion."""


# Counting number of conversions per source
conversions_by_channel = conversion.groupby('Source Id').size().reset_index()
conversions_by_channel.columns = ['Source Id', 'Conversions']

sns.barplot(data=conversions_by_channel, x='Source Id', y='Conversions', palette=palette)
plt.title('Conversions per Marketing Source')
plt.xlabel('Source')
plt.ylabel('Quantity')
plt.legend([],[], frameon=False)
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/conversion_by_channel.png", dpi=150)
plt.close()
print(conversions_by_channel.sort_values(by='Conversions'))

# When each source first appeared?
first_appearance = conversion.groupby('Source Id')['First Session Date'].min()
print("Frist appareance of each source")
print(first_appearance.sort_values())

"""Marketing channel 7 only had one conversion. To rule out that this result was due to a late implementation of this channel, I checked the first appearance of each channel. And although channel 7 was indeed implemented two months after the other channels, it shows very low performance. Nine months is more than enough time to generate more than one conversion if this channel were effective. Channel 7 has a clear performance problem, and it's important that the marketing team provide more information to understand what's happening."""

# How many orders do they place during a given period of time?

## Transforming 'Buy Date' column to datetime
orders['Buy Date'] = pd.to_datetime(orders['Buy Date'])

## Creating 'Buy Month' column to aggrupate by month
orders['Buy Month'] = orders['Buy Date'].dt.month

## Aggrupate and count
purchases_per_month = orders.groupby('Buy Month')['Uid'].size().reset_index()

## Graph and display data
sns.barplot(data=purchases_per_month, x='Buy Month', y='Uid', color='skyblue')
plt.title('Total purchases per month')
plt.xlabel('Month')
plt.ylabel('Number of Purchases')
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/purchases_per_month.png", dpi=150)
plt.close()

print()
print(purchases_per_month.sort_values(by='Uid', ascending=False))
print()

"""The last three months of the year (December, November, and October) see the highest total sales. Most events are likely to take place during this time. The three months with the fewest sales are August, June, and July, probably because there are fewer events during this period or people prefer to travel during the summer rather than buy event tickets."""

# Average size of purchase

## Aggrupate by unique Uid and sum the revenue
revenue_per_user = orders.groupby('Uid').agg({
    'Revenue':'sum'
}).reset_index()

### Identificar el promedio de compra
average_revenue = revenue_per_user['Revenue'].mean()

print(f'Average purchase size: ${average_revenue:.2f}.')

## LTV por cohorte
user_cohorts = visits.groupby('Uid').agg({
    'First Session Year': 'first',
    'First Session Month': 'first'
}).reset_index()

cohorts_revenue = user_cohorts.merge(orders[['Uid', 'Revenue']], on='Uid')

ltv_by_cohort = cohorts_revenue.groupby(['First Session Year', 'First Session Month']).agg(
    total_revenue=('Revenue', 'sum'),
    num_users=('Uid', 'nunique')
).reset_index()

ltv_by_cohort['LTV'] = ltv_by_cohort['total_revenue'] / ltv_by_cohort['num_users']


cohorts_plot_month_year(ltv_by_cohort, 2017, 2017, 'First Session Year', 'First Session Month', 'LTV')
cohorts_plot_month_year(ltv_by_cohort, 2018, 2018, 'First Session Year', 'First Session Month', 'LTV')
plt.title('Average Life Time Value per cohort 2017 - 2018')
plt.xlabel('Cohort Month')
plt.ylabel('LTV ($)')
plt.legend()
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/ltv_cohorts.png", dpi=150)
plt.close()
print()

print()
print(ltv_by_cohort.sort_values(by='LTV', ascending=False))

"""It's clear that the cohort with the highest LTV is the first cohort (January 2017). This makes sense since they had been interacting with the platform and familiar with the site for a longer period. However, there's a drastic change for the February cohort of that same year; now, customers have an LTV of $7.44, compared to $29.60 for users in the January cohort. Unfortunately, all subsequent cohorts continued to exhibit the same behavior, and no LTV ever exceeded $10.00.
"""

## LTV per marketing source

channels_revenue = visits.merge(orders[['Revenue', 'Uid']]).reset_index()

ltv_by_channel = channels_revenue.groupby(['Source Id']).agg(
   total_revenue=('Revenue', 'sum'),
   num_users=('Uid', 'nunique')
).reset_index()

ltv_by_channel['LTV'] = ltv_by_channel['total_revenue'] / ltv_by_channel['num_users']

sns.barplot(data=ltv_by_channel, x='Source Id', y='LTV', palette = palette)
plt.title('Average Life Time Value per marketing source')
plt.xlabel('Marketing Source')
plt.ylabel(' Average LTV ($)')
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/ltv_marketing_channel.png", dpi=150)
plt.close()

print()
print(ltv_by_channel.sort_values(by='LTV', ascending=False))

"""The best marketing channel is undoubtedly channel #2, which has achieved an average of $361.14. While it doesn't have the highest number of conversions, it is the most attractive channel for users who make larger or more frequent purchases. This is the channel that has generated the greatest monetary value.
"""

## LTV per device

device_revenue = visits.merge(orders[['Revenue', 'Uid']]).reset_index()

ltv_by_device = device_revenue.groupby(['Device']).agg(
   total_revenue=('Revenue', 'sum'),
   num_users=('Uid', 'nunique')
).reset_index()

ltv_by_device['LTV'] = ltv_by_device['total_revenue'] / ltv_by_device['num_users']

sns.barplot(data=ltv_by_device, x='Device', y='LTV', color='skyblue')
plt.title('Average Life Time Value) per device')
plt.xlabel('Device')
plt.ylabel('Average LTV ($)')
plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.savefig("figures/ltv_device.png", dpi=150)
plt.close()

print()
print(ltv_by_device.sort_values(by='LTV', ascending=False))

"""Customers prefer using the desktop version of the website to make purchases; it's likely more user-friendly, which inspires more trust. The price difference is $152.99. It's important to review the mobile version.
"""

## 3. Marketing


# Money spent:   Total / per acquisition source / over time
costs['month'] = costs['dt'].dt.month
costs['year'] = costs['dt'].dt.isocalendar().year

costs_marketing_monthly = costs.groupby(['source_id', 'month', 'year']).agg({
     'costs':'sum'
}).reset_index()


print(costs_marketing_monthly)

def costs_marketing_month_year(df, channel, label):
    plot = df[df['source_id'] == channel]
    return sns.lineplot(data=plot, x= 'month', y= 'costs', label=label)

costs_marketing_month_year(costs_marketing_monthly, 1, 1)
costs_marketing_month_year(costs_marketing_monthly, 2, 2)
costs_marketing_month_year(costs_marketing_monthly, 3, 3)
costs_marketing_month_year(costs_marketing_monthly, 4, 4)
costs_marketing_month_year(costs_marketing_monthly, 5, 5)
costs_marketing_month_year(costs_marketing_monthly, 6, 6)
costs_marketing_month_year(costs_marketing_monthly, 7, 7)
costs_marketing_month_year(costs_marketing_monthly, 8, 8)
costs_marketing_month_year(costs_marketing_monthly, 9, 9)
costs_marketing_month_year(costs_marketing_monthly, 10, 10)

plt.title('Money spent per acquisition source over time')
plt.xlabel('Month')
plt.ylabel('Cost ($)')

# 2. Acquisition cost of customers per source
## CAC = Total spending from that source / Number of unique users acquired from that source

total_marketing_costs = costs_marketing_monthly.groupby('source_id')['costs'].sum()

users_per_channel = visits.groupby('Source Id')['Uid'].nunique()

cac = (total_marketing_costs / users_per_channel).fillna(0)
cac.name = 'CAC'
cac

"""The most expensive sources: (Higher CAC):
- Source 3: 1.89 per customer
- Source 2: 1.63 per customer  
- Source 1: 1.10 per customer

The most efficient sources: (Lower CAC):
- Source 9: 0.60 per customer
- Source 10: 0.72 per customer
- Source 4: 0.73 per customer

Problematic sources:
- Sources 6 and 7: CAC = 0.00
"""

total_marketing_costs = (
    costs_marketing_monthly
    .groupby('source_id')['costs']
    .sum()
    .to_frame(name='costs')
)

total_marketing_costs.index.name = 'Source Id'


ltv_aligned = ltv_by_channel['LTV'].reindex(total_marketing_costs.index, fill_value=0)

romi = (ltv_aligned / total_marketing_costs['costs']).rename('ROMI')

romi_df = pd.concat([ltv_aligned.rename('LTV'), total_marketing_costs, romi], axis=1)
print(romi_df)

ax = sns.barplot(
    data=romi_df.reset_index(),
    x='Source Id', y='ROMI',
    errorbar=None,
    color='skyblue'
)


ax.bar_label(ax.containers[0], fmt='%.3f', padding=3)
plt.title('ROMI per Marketing Source')
plt.xlabel('Marketing Source')
plt.ylabel('ROMI (LTV / Costs)')
plt.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
plt.tight_layout()
plt.tight_layout()
plt.savefig("figures/romi_marketing_source.png", dpi=150)
plt.close()

"""After analyzing the performance results by marketing channel, significant differences were observed in both customer acquisition costs (CAC) and return on investment (ROMI) for each source.

First, the channels with the highest investment (for example, channels 2 and 3) did not necessarily show a proportional return, exhibiting a low ROMI. This indicates that, although they generate users, their cost per acquisition is high and not profitable in terms of return on investment.

On the other hand, channels such as 1 and 5 presented a better balance between cost and lifetime value (LTV), showing a reasonable CAC and a higher ROMI compared to the others. This suggests that these channels are more efficient at converting investment into revenue.

In this analysis, the key metrics used were:

Total cost per channel → to identify the channels with the highest spending.

CAC (Customer Acquisition Cost) → to measure acquisition efficiency.

LTV (Lifetime Value) → to estimate the average value of each customer."""''