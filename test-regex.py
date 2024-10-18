import re

text = input("Enter command: ")
cat_sub_pattern = f"(adventure|action|thriller|horror|comedy|musical|romance|drama|fantasy)"
pattern = re.compile(r"^\$movie( "+cat_sub_pattern+r")((,|-)"+cat_sub_pattern+r"){0,2}$")    
help_pattern = re.compile(r"^\$movie( -help)?$")

if pattern.fullmatch(text):
    print("Matched!")
else:
    print("Not Matched")