path = r'D:\$RECYCLE.BIN\S-1-5-21-60695564-3632225826-2738181695-1001\$R1Y4BJ0.py'
try:
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read(1000))
except Exception as e:
    print(f"Error: {e}")
