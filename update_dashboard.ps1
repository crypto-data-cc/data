python main.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tokenized_stocks.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python build_dashboard.py
exit $LASTEXITCODE
