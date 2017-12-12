import hashlib
import random
total_valid_guesses = 100

def complexity_function(input_number):
  hash_val = hashlib.sha256(bytes(str(input_number)))
  hash_str = hash_val.hexdigest()
  # return hash_str[:5] == '00000'
  return hash_str[:3] == '000'
  # return hash_str[:6] == '000000' or hash_str[:6] == '000001' or hash_str[:6] == '000002' or hash_str[:6] == '000003'

total_guesses = 0
valid_guesses = 0

while valid_guesses < total_valid_guesses:
  total_guesses += 1
  guess = random.randint(0, 2**31)
  if complexity_function(guess):
    valid_guesses += 1
    print valid_guesses

print total_guesses/float(total_valid_guesses)
