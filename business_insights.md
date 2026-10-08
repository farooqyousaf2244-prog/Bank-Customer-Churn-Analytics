# Business Insights and Recommendations

Overall churn: **20.37%** (2,037 of 10,000 customers). Customers who left held **EUR 185.6M** in balances, **24.3%** of the total.
All figures come from `outputs/*.csv`, produced by the pipeline and reconciled by the SQL queries in `sql/`.

## Where churn is concentrated

| # | Finding | Evidence | Lift vs overall |
|---|---|---|---|
| 1 | **Germany is the highest-risk market** | 32.4% churn; 25% of customers but 40% of all churners | 1.59x |
| 2 | **Customers aged 46-65 churn at about half** | 46-55: 50.6%, 56-65: 48.3%, versus 7.5-8.5% under 35. These two groups are 18% of customers and 45% of churners | 2.4-2.5x |
| 3 | **Single-product customers drive volume** | 27.7% churn; 69% of all churners | 1.36x |
| 4 | **3-4 product customers almost always leave** | 3 products: 82.7%, 4 products: 100% (326 customers, 280 churned) | 4.1-4.9x |
| 5 | **Inactive members churn about twice as often** | 26.9% vs 14.3% active | 1.32x vs 0.70x |
| 6 | **Women churn more than men** | 25.1% vs 16.5% | 1.23x vs 0.81x |
| 7 | **Credit score is a weak signal** | 18.6%-22.0% across all bands | about 1.0x |

Highest-risk combination: **inactive customers in Germany at 41.1% churn** (Spain: 23.3%, France: 21.1%).
Two products (7.6% churn) is the healthiest segment.

## Recommendations

1. **Germany retention programme.** Start with inactive German customers (518 churned of 1,261). Investigate local pricing, service and competitor offers before choosing the incentive.
2. **Proactive outreach to ages 46-65.** Build a relationship-manager or tailored-offer journey for this age band; it holds nearly half of all churn.
3. **Cross-sell from 1 to 2 products.** The 2-product group churns at under a third of the single-product rate. Treat this as a hypothesis to test (correlation, not proven cause).
4. **Investigate the 3-4 product group.** A churn rate this high suggests a product, bundling or mis-selling problem. Review before any push to sell more products.
5. **Re-engage inactive high-balance customers.** 1,584 customers who have not churned are inactive with balances of EUR 100k or more, holding EUR 210.6M. Query 10 in `sql/02_analysis.sql` lists them by country.
6. **Win-back list.** Query 9 returns the 20 highest-balance churned customers.

## Limitations

- This is descriptive analysis. It shows where churn is high, not why, and no predictive model is built.
- Segments overlap (for example, age and product count); rates are not additive.
- The `HasCrCard` / `IsActiveMember` anomaly (see `data_quality_report.md`) must be resolved before the activity insight is relied on for budget decisions.
- No time dimension in the data, so trends and seasonality cannot be assessed.
