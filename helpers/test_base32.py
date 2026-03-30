from core.constants import to_base_32
from colorama import Fore

print(Fore.BLUE + f"0 -> {to_base_32(0)}")
print(Fore.RED + f"1 -> {to_base_32(1)}")
print(Fore.WHITE + f"32 -> {to_base_32(32)}")
print(f"1023 -> {to_base_32(1023)}")
print(f"123.45 -> {to_base_32(123.45)}")
