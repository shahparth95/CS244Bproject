import hashlib
import random
import time
total_valid_guesses = 100

def complexity_function(input_number):
  hash_val = hashlib.sha256(bytes(str(input_number)))
  hash_str = hash_val.hexdigest()
  return hash_str[:5] == '00000'    # Complexity : 2 * 10^-6
  # return hash_str[:4] == '0000'    # Complexity : 2 * 10^-5
  # return hash_str[:3] == '000'   # Complexity : 2 * 10^-4
  # return hash_str[:6] == '000000' or hash_str[:6] == '000001' or hash_str[:6] == '000002' or hash_str[:6] == '000003'

total_guesses = 0
valid_guesses = 0
startTime = time.time()
endTime = 0
timeTaken = 0

while valid_guesses < total_valid_guesses:
  total_guesses += 1
  guess = random.randint(0, 2**31)
  if complexity_function(guess):
    endTime = time.time()
    valid_guesses += 1
    timeTaken += endTime - startTime
    print valid_guesses
    startTime = time.time()

print timeTaken/float(total_valid_guesses)
