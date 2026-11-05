
import traceback
try:
    with open('scratch/quick_test3.log', 'r') as f:
        print(f.read())
except Exception as e:
    print(e)
