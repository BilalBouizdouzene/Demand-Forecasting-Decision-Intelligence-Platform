# M5 raw data

This project uses the real public **M5 Forecasting - Accuracy** retail dataset. Place these files in this directory:

- `sales_train_validation.csv`
- `calendar.csv`
- `sell_prices.csv`

The preferred reproducible command is:

```powershell
python scripts/download_data.py
```

The script first tries the Kaggle API when `KAGGLE_USERNAME` and `KAGGLE_KEY` (or `KAGGLE_API_TOKEN`) are configured, then tries the public Zenodo record documented in the script. If neither route is available, download the files from the [M5 Forecasting - Accuracy competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data) or the public [Zenodo M5 record](https://doi.org/10.5281/zenodo.10203108), and copy the three files here. Do not rename them.

The raw files are intentionally ignored by Git because the dataset is hundreds of megabytes. The acquisition script records file sizes, hashes, and schema checks in `results/reports/data_acquisition.json`.
