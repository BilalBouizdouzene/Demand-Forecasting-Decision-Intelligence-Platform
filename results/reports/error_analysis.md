# Forecast error analysis

This report is generated from actual forecast residuals; it does not infer causal explanations.

```text
       value      mae      bias  rows      dimension
 high_volume 1.096168  0.965420  3712 demand_segment
       FOODS 0.568831  0.062078  2240         cat_id
        CA_3 0.306209  0.034269  2800       store_id
        CA_2 0.292500  0.020000  2800       store_id
        CA_1 0.286127  0.028141  2800       store_id
        TX_2 0.278911  0.011674  2800       store_id
        WI_1 0.276996  0.017133  2800       store_id
           1 0.272107 -0.031382  2000     event_flag
        TX_3 0.257162  0.015099  2800       store_id
           0 0.256180  0.019634 26000     event_flag
     HOBBIES 0.245479  0.012998 10920         cat_id
        WI_2 0.241105  0.011200  2800       store_id
        WI_3 0.234111  0.002869  2800       store_id
   HOUSEHOLD 0.219008  0.011235 14840         cat_id
        TX_1 0.202148  0.006660  2800       store_id
        CA_4 0.197910  0.012855  2800       store_id
intermittent 0.129114 -0.129114 24288 demand_segment
```

## Largest failures

```text
      date store_id         item_id    cat_id  actual  forecast  event_flag demand_segment     error  absolute_error     direction
2016-03-03     WI_2     FOODS_2_289     FOODS    18.0  5.658207           0    high_volume 12.341793       12.341793 underforecast
2016-03-19     CA_2     FOODS_2_289     FOODS    12.0  1.119684           0    high_volume 10.880316       10.880316 underforecast
2016-03-12     TX_3   HOBBIES_1_248   HOBBIES    10.0  1.417580           0    high_volume  8.582420        8.582420 underforecast
2016-03-05     TX_1     FOODS_2_289     FOODS     8.0  0.790280           0    high_volume  7.209720        7.209720 underforecast
2016-03-03     CA_3     FOODS_1_118     FOODS     8.0  0.824698           0    high_volume  7.175302        7.175302 underforecast
2016-03-01     TX_3 HOUSEHOLD_1_386 HOUSEHOLD    11.0  3.962085           0    high_volume  7.037915        7.037915 underforecast
2016-03-12     CA_3   HOBBIES_1_248   HOBBIES     8.0  1.016471           0    high_volume  6.983529        6.983529 underforecast
2016-03-04     WI_2     FOODS_2_289     FOODS     1.0  7.665307           0    high_volume -6.665307        6.665307  overforecast
2016-03-14     CA_3     FOODS_2_071     FOODS     7.0  0.424902           0    high_volume  6.575098        6.575098 underforecast
2016-03-15     WI_2     FOODS_2_289     FOODS     0.0  6.520535           0   intermittent -6.520535        6.520535  overforecast
2016-03-26     WI_3     FOODS_2_289     FOODS     9.0  2.621337           0    high_volume  6.378663        6.378663 underforecast
2016-03-25     CA_3     FOODS_2_289     FOODS     8.0  1.723103           0    high_volume  6.276897        6.276897 underforecast
2016-03-19     CA_1     FOODS_2_071     FOODS     7.0  0.769335           0    high_volume  6.230665        6.230665 underforecast
2016-03-25     WI_2   HOBBIES_1_248   HOBBIES     9.0  2.797206           0    high_volume  6.202794        6.202794 underforecast
2016-03-25     CA_1     FOODS_1_118     FOODS     7.0  0.897774           0    high_volume  6.102226        6.102226 underforecast
2016-03-12     CA_1   HOBBIES_1_248   HOBBIES     7.0  0.990037           0    high_volume  6.009963        6.009963 underforecast
2016-03-09     WI_1   HOBBIES_2_047   HOBBIES     6.0  0.026913           0    high_volume  5.973087        5.973087 underforecast
2016-03-13     CA_1   HOBBIES_2_014   HOBBIES     6.0  0.064721           0    high_volume  5.935279        5.935279 underforecast
2016-03-02     WI_2   HOBBIES_1_248   HOBBIES    10.0  4.067297           0    high_volume  5.932703        5.932703 underforecast
2016-03-21     CA_1 HOUSEHOLD_2_365 HOUSEHOLD     6.0  0.083232           0    high_volume  5.916768        5.916768 underforecast
```
