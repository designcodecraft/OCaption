import winshell

try:
    for item in winshell.recycle_bin():
        print(f"Name: {item.original_filename()}")
        print(f"Path: {item.real_filename()}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
