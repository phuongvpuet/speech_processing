import re 

pattern1 = re.compile(r"[.]\n+|\n")
pattern2 = re.compile(r"[.]+\s|\n")

#OPen text
with open("Giai_tri.txt", "r", encoding='utf-8') as f:
    texts = f.read()

#Tach thanh tung doan nho 
blocks = re.split(pattern1, texts)

#Tach cac cau trong doan nho
result = []
for block in blocks:
    result += re.split(pattern2, block)
result = [res for res in result if res != '']
#Print ket qua
for id, res in enumerate(result):
    print(id,"-->", res)