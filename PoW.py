from hashlib import sha256
from time import time

x = 5
y = 0

start = time()
while sha256(f'{x * y}'.encode()).hexdigest()[:6] != '000000':
    y += 1
    print(f'y = {y}')

end = time()
print(f'The solution is y = {y}')
print(f'Time taken = {(end - start)/60.0}')
