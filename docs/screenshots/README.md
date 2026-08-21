# Screenshot checklist

This folder is reserved for the images used in the project README, CV, and presentation slides. The application does not depend on these files.

## Capture order

Start the web application from the repository root:

~~~powershell
./.venv/Scripts/python.exe -m uvicorn --app-dir src demand_intelligence.api.main:app --reload --port 8000
~~~

Use a browser at roughly 1440 × 900 pixels and keep the zoom at 100%. Avoid including a terminal, local file paths, or personal information in the frame.

## Required images

| File | Page | What should be visible |
| --- | --- | --- |
| 01-overview.png | Overview | KPI cards, forecast horizon, planner brief, and priority queue |
| 02-forecast-explorer.png | Forecast explorer | Store and item selection, chart, uncertainty range, and daily output |
| 03-decision-center.png | Decision center | Critical or High filter, risk pills, order quantities, and priority scores |
| 04-model-performance.png | Model performance | WAPE chart, benchmark table, and deployed Ridge information |
| 05-monitoring.png | Monitoring | MAE trend, drift table, and current retraining decision |
| 06-api-docs.png | Swagger | Optional: one expanded forecast endpoint at /docs |

## Naming and format

- Use PNG format.
- Keep the names exactly as listed above.
- Crop the browser content rather than the entire desktop.
- Use the same theme and browser size for every capture.
- Add the files to Git only when they are useful for the project presentation; they are optional for running the code.
